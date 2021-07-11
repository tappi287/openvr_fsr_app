import os
import logging
import sys
import json
from pathlib import Path
from typing import Union

from appdirs import user_log_dir, user_data_dir

from .knownpaths import get_current_user_documents_path

OPEN_VR_DLL = 'openvr_api.dll'
OPEN_VR_FSR_CFG = 'openvr_mod.cfg'
APP_NAME = 'openvr_fsr_app'
DATA_DIR = 'data'
APP_FRIENDLY_NAME = 'OpenVR FSR App'
SETTINGS_DIR_NAME = 'openvr_fsr_app'

BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__ + '/..')))

GIT_RELEASE_URL = 'https://api.github.com/repos/tappi287/rf2_video_settings/releases/latest'

UPDATE_VERSION_FILE = 'version.txt'
UPDATE_INSTALL_FILE = 'rF2_Settings_Wizard_{version}_win64.exe'

DEFAULT_LOG_LEVEL = 'DEBUG'

KNOWN_APPS = {
    "365960": {
        "name": "rFactor 2",
        "installdir": "rFactor 2",
        "executable": "rFactor2.exe",
        "exe_sub_path": "Bin64/",
    },
    "908520": {
        "name": "fpsVR",
        "installdir": "fpsVR",
        "executable": "fpsVR.exe",
        "exe_sub_path": ""
    }
}

RF2_APPID = [k for k in KNOWN_APPS.keys()][0]

# Frozen or Debugger
if getattr(sys, 'frozen', False):
    # -- Running in PyInstaller Bundle ---
    FROZEN = True
else:
    # -- Running in IDE ---
    FROZEN = False

SETTINGS_FILE_NAME = 'settings.json' if FROZEN else 'settings_dev.json'


def check_and_create_dir(directory: Union[str, Path]) -> str:
    if not os.path.exists(directory):
        try:
            os.mkdir(directory)
            logging.info('Created: %s', directory)
        except Exception as e:
            logging.error('Error creating directory %s', e)
            return ''

    return directory


def get_current_modules_dir() -> str:
    """ Return path to this app modules directory """
    return BASE_PATH


def get_settings_dir() -> Path:
    return Path(check_and_create_dir(user_data_dir(SETTINGS_DIR_NAME, '')))


def _get_user_doc_dir() -> Path:
    docs_dir = get_current_user_documents_path()
    if not docs_dir:
        docs_dir = os.path.expanduser('~\\Documents\\')
    return Path(docs_dir)


def get_data_dir() -> Path:
    return Path(get_current_modules_dir()) / DATA_DIR


def get_log_dir() -> str:
    log_dir = user_log_dir(SETTINGS_DIR_NAME, '')
    setting_dir = os.path.abspath(os.path.join(log_dir, '../'))
    # Create <app-name>
    check_and_create_dir(setting_dir)
    # Create <app-name>/log
    return check_and_create_dir(log_dir)


def get_log_file() -> Path:
    if FROZEN:
        return Path(get_log_dir()) / f'{APP_NAME}.log'
    else:
        return Path(get_log_dir()) / f'{APP_NAME}_DEV.log'


def get_version() -> str:
    f = Path('.') / 'package.json'
    if f.is_file():
        try:
            with open(f.as_posix(), 'r') as f:
                pkg = json.load(f)
                return pkg.get('version')
        except Exception as e:
            print('Duh!', e)

    f = Path('../modules') / 'version.txt'
    try:
        with open(f.as_posix(), 'r') as f:
            version = f.read()
            return version
    except Exception as e:
        print('Duh!', e)

    return '0.0.0'


