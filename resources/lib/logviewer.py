# -*- coding: utf-8 -*-

import threading

import xbmc
import xbmcgui

from resources.lib.command_runner import CommandRunner
from resources.lib.utils import ADDON_PATH

# Action IDs for closing the window
ACTION_PARENT_DIR = 9
ACTION_PREVIOUS_MENU = 10
KEY_NAV_BACK = 92
ACTION_STOP = 13
ACTION_BACKSPACE = 110


class TextWindow(xbmcgui.WindowXMLDialog):
    """Full-screen window that streams command output into a TextBox with periodic refresh."""

    def __init__(self, xml_filename, script_path, title, command, max_lines=100, refresh_ms=200):
        super(TextWindow, self).__init__(xml_filename, script_path)
        self.title = title
        self.command = command
        self.max_lines = max_lines
        self.refresh_ms = refresh_ms
        self._runner = None
        self._closing = False
        # Control IDs (matching the skin XML)
        self.close_button_id = 32500
        self.title_label_id = 32501
        self.text_box_id = 32503

    def onInit(self):
        self.getControl(self.title_label_id).setLabel(self.title)
        self.getControl(self.text_box_id).setText("Loading...")
        # Start the command
        self._runner = CommandRunner(self.command, max_lines=self.max_lines)
        self._runner.start()
        # Start the refresh loop in a background thread
        self._poll_thread = threading.Thread(target=self._poll_loop, daemon=True)
        self._poll_thread.start()

    def _poll_loop(self):
        """Background polling loop - reads data and updates the textbox."""
        monitor = xbmc.Monitor()
        while not self._closing and not monitor.abortRequested():
            # Use short sleep intervals so we can react to close quickly
            if monitor.waitForAbort(self.refresh_ms / 1000.0):
                break
            if self._closing:
                break
            if self._runner is None:
                break
            text = self._runner.get_text()
            if text is not None:
                try:
                    self.getControl(self.text_box_id).setText(text)
                except RuntimeError:
                    break

    def _request_close(self):
        """Signal the poll loop to stop, then close the window."""
        self._closing = True
        if self._runner is not None:
            self._runner.stop()
            self._runner = None
        self.close()

    def onClick(self, control_id):
        if control_id == self.close_button_id:
            self._request_close()

    def onAction(self, action):
        action_id = action.getId()
        if action_id in (ACTION_PARENT_DIR, KEY_NAV_BACK, ACTION_PREVIOUS_MENU,
                         ACTION_STOP, ACTION_BACKSPACE):
            self._request_close()


FONT_SIZE_XMLS = {
    "0": "script.logviewer-textwindow-small.xml",
    "1": "script.logviewer-textwindow-medium.xml",
    "2": "script.logviewer-textwindow-large.xml",
}


def show_command_output(title, command, max_lines=100, refresh_ms=200, font_size="1"):
    """Show a streaming command output window."""
    xml_file = FONT_SIZE_XMLS.get(font_size, FONT_SIZE_XMLS["1"])
    w = TextWindow(
        xml_file,
        ADDON_PATH,
        title=title,
        command=command,
        max_lines=max_lines,
        refresh_ms=refresh_ms,
    )
    w.doModal()
    # Ensure cleanup if window closed externally
    w._closing = True
    if w._runner is not None:
        w._runner.stop()
    del w
