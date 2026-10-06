# -*- coding: utf-8 -*-

import sys
import time
import unittest

sys.path.insert(0, ".")

from resources.lib.command_runner import CommandRunner


class TestCommandRunner(unittest.TestCase):
    def test_basic_output(self):
        """Command output is captured."""
        r = CommandRunner("echo hello", max_lines=10)
        r.start()
        time.sleep(0.5)
        text = r.get_text()
        r.stop()
        self.assertIsNotNone(text)
        self.assertIn("hello", text)

    def test_dirty_flag(self):
        """get_text returns None when no new data since last call."""
        r = CommandRunner("echo hello", max_lines=10)
        r.start()
        time.sleep(0.5)
        t1 = r.get_text()
        t2 = r.get_text()
        r.stop()
        self.assertIsNotNone(t1)
        self.assertIsNone(t2)

    def test_ring_buffer(self):
        """Ring buffer keeps only the last max_lines lines."""
        # Use a command that outputs 20 lines
        if sys.platform == "win32":
            cmd = 'cmd /c "for /L %i in (1,1,20) do @echo %i"'
        else:
            cmd = "seq 1 20"
        r = CommandRunner(cmd, max_lines=5)
        r.start()
        time.sleep(2)
        text = r.get_text()
        r.stop()
        self.assertIsNotNone(text)
        lines = [l for l in text.strip().split("\n") if l]
        self.assertEqual(len(lines), 5)
        self.assertIn("20", lines[-1])

    def test_is_running(self):
        """is_running returns False after process exits."""
        r = CommandRunner("echo done", max_lines=10)
        r.start()
        time.sleep(0.5)
        self.assertFalse(r.is_running())
        r.stop()

    def test_stop_kills_process(self):
        """stop() terminates a long-running process."""
        if sys.platform == "win32":
            cmd = "ping -n 100 127.0.0.1"
        else:
            cmd = "sleep 100"
        r = CommandRunner(cmd, max_lines=10)
        r.start()
        time.sleep(0.3)
        self.assertTrue(r.is_running())
        r.stop()
        self.assertFalse(r.is_running())


if __name__ == "__main__":
    unittest.main()
