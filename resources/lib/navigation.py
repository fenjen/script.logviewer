# -*- coding: utf-8 -*-

import json
import os
import sys

import xbmcgui

from resources.lib import logviewer, utils


def get_kodi_log_path():
    """Detect the Kodi log file path using Kodi's own APIs."""
    try:
        import xbmc
        import xbmcvfs
        log_path = xbmcvfs.translatePath("special://logpath")
        # Get app name via JSON-RPC
        cmd = ('{"jsonrpc":"2.0", "method":"Application.GetProperties",'
               '"params": {"properties": ["name"]}, "id":1}')
        data = json.loads(xbmc.executeJSONRPC(cmd))
        if "result" in data and "name" in data["result"]:
            app_name = data["result"]["name"].lower()
        else:
            app_name = "kodi"
        return os.path.join(log_path, "{}.log".format(app_name))
    except Exception:
        return None


def get_default_command():
    """Build a default tail command for the Kodi log."""
    path = get_kodi_log_path()
    if path and os.path.isfile(path):
        return "tail -n 100 -f {}".format(path)
    return ""


def show_output():
    command = utils.get_setting("command")
    if not command:
        # Try auto-detecting kodi log
        command = get_default_command()
    if not command:
        xbmcgui.Dialog().ok(utils.ADDON_NAME, "No command configured. Please set a command in the add-on settings.")
        utils.open_settings()
        return
    max_lines = utils.get_int_setting("max_lines")
    refresh_ms = utils.get_int_setting("refresh_ms")
    font_size = utils.get_setting("font_size")
    logviewer.show_command_output(utils.ADDON_NAME, command, max_lines=max_lines, refresh_ms=refresh_ms, font_size=font_size)


def run():
    if len(sys.argv) > 1:
        method = sys.argv[1]
        if method == "show_output":
            show_output()
        elif method == "settings":
            utils.open_settings()
        else:
            raise NotImplementedError("Method '{}' does not exist".format(method))
    else:
        # Launch directly — settings are accessible via Kodi's addon configure button
        show_output()
