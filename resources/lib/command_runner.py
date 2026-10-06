# -*- coding: utf-8 -*-

import os
import signal
import subprocess
import threading
from collections import deque

POSIX = os.name == "posix"


class CommandRunner(object):
    """Runs a shell command and streams stdout into a ring buffer of the last N lines.

    stop() is designed to return quickly even when the command is idle (e.g.
    ``tail -f`` on a quiet log). The reader thread parks inside a blocking
    readline(), so the only reliable way to wake it is to close the write end of
    the pipe -- i.e. kill the process. The pipe object itself is never touched
    from outside the reader thread: BufferedReader.close() would block on the
    same internal lock that readline() is holding.
    """

    def __init__(self, command, max_lines=500):
        self._command = command
        self._max_lines = max_lines
        self._buffer = deque(maxlen=max_lines)
        self._lock = threading.Lock()
        self._process = None
        self._reader_thread = None
        self._running = False
        self._dirty = False

    def start(self):
        """Start the subprocess and the background reader thread."""
        if self._process is not None:
            raise RuntimeError("CommandRunner already started")

        self._running = True

        # Put the command in its own process group / job so we can kill the
        # whole pipeline later, not just the shell that spawned it.
        kwargs = {}
        if POSIX:
            kwargs["start_new_session"] = True
        else:
            kwargs["creationflags"] = subprocess.CREATE_NEW_PROCESS_GROUP

        self._process = subprocess.Popen(
            self._command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL,
            shell=True,
            close_fds=True,
            **kwargs
        )

        # The process is passed explicitly so the reader never races with
        # stop() setting self._process to None.
        self._reader_thread = threading.Thread(
            target=self._read_loop,
            args=(self._process,),
            daemon=True,
        )
        self._reader_thread.start()

    def stop(self, timeout=2):
        """Kill the command and let the reader thread unwind.

        Bounded by ``timeout`` twice in the worst case; normally returns in
        milliseconds. Safe to call more than once.
        """
        self._running = False

        process, self._process = self._process, None
        thread, self._reader_thread = self._reader_thread, None

        if process is not None:
            self._kill(process)
            try:
                process.wait(timeout=timeout)
            except Exception:
                pass

        if thread is not None and thread is not threading.current_thread():
            thread.join(timeout=timeout)

    def get_text(self):
        """Return the buffer as a single string, or None if unchanged since the last call."""
        with self._lock:
            if not self._dirty:
                return None
            self._dirty = False
            return "\n".join(self._buffer)

    def is_running(self):
        """True while the subprocess is still alive."""
        process = self._process
        if process is None:
            return False
        return process.poll() is None

    # ------------------------------------------------------------------ #
    # internals
    # ------------------------------------------------------------------ #

    @staticmethod
    def _kill(process):
        """Kill the whole process group, falling back to the direct child.

        With shell=True and a pipeline, process.pid may be the shell rather than
        the command actually holding the pipe open. Killing only part of the
        pipeline is not enough: the survivors keep the write end open and the
        reader stays blocked until the next line (or forever).
        """
        if process.poll() is not None:
            return

        try:
            if POSIX:
                os.killpg(os.getpgid(process.pid), signal.SIGKILL)
            else:
                subprocess.call(
                    ["taskkill", "/F", "/T", "/PID", str(process.pid)],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                )
            return
        except Exception:
            pass

        try:
            process.kill()
        except OSError:
            pass

    def _read_loop(self, process):
        """Background thread: read lines from stdout into the ring buffer."""
        stdout = process.stdout
        try:
            for raw_line in iter(stdout.readline, b""):
                if not self._running:
                    break
                line = raw_line.decode("utf-8", errors="replace").rstrip("\r\n")
                with self._lock:
                    self._buffer.append(line)
                    self._dirty = True
        except (OSError, ValueError):
            # Pipe closed underneath us -- expected during stop().
            pass
        finally:
            # Closing from this thread is safe; from any other thread it would
            # block on the buffer lock held by readline().
            try:
                stdout.close()
            except OSError:
                pass
