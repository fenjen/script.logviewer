# -*- coding: utf-8 -*-

import logging

import xbmc
import xbmcaddon

ADDON = xbmcaddon.Addon()
ADDON_PATH = ADDON.getAddonInfo("path")
ADDON_NAME = ADDON.getAddonInfo("name")
ADDON_ID = ADDON.getAddonInfo("id")


def get_setting(setting):
    return ADDON.getSetting(setting)


def get_int_setting(setting):
    return int(get_setting(setting))


def open_settings():
    ADDON.openSettings()


class KodiLogHandler(logging.StreamHandler):
    levels = {
        logging.CRITICAL: xbmc.LOGFATAL,
        logging.ERROR: xbmc.LOGERROR,
        logging.WARNING: xbmc.LOGWARNING,
        logging.INFO: xbmc.LOGINFO,
        logging.DEBUG: xbmc.LOGDEBUG,
        logging.NOTSET: xbmc.LOGNONE,
    }

    def __init__(self):
        super(KodiLogHandler, self).__init__()
        self.setFormatter(logging.Formatter("[{}] %(message)s".format(ADDON_ID)))

    def emit(self, record):
        xbmc.log(self.format(record), self.levels[record.levelno])

    def flush(self):
        pass


def set_logger(name=None, level=logging.DEBUG):
    logger = logging.getLogger(name)
    logger.addHandler(KodiLogHandler())
    logger.setLevel(level)
