import os
import logging
import re
import sys
import json
from pathlib import Path
from typing import Union

from appdirs import user_log_dir, user_data_dir

from app.util.knownpaths import get_current_user_documents_path

OPEN_VR_DLL = 'openvr_api.dll'
DXGI_DLL = 'dxgi.dll'
EXE_NAME = '*.exe'
OPEN_VR_FSR_CFG = 'openvr_mod.cfg'
VRPERFKIT_CFG = 'vrperfkit.yml'
APP_NAME = 'openvr_fsr_app'
DATA_DIR = 'data'
SETTINGS_DIR_NAME = 'openvr_fsr_app'
USER_APP_PREFIX = 'Usr'
CUSTOM_APP_PREFIX = '#'

BASE_PATH = getattr(sys, '_MEIPASS', os.path.dirname(os.path.abspath(__file__ + '/..')))

UPDATE_VERSION_FILE = 'version.txt'
UPDATE_INSTALL_FILE = 'OpenVR-FSR-App_{version}_win64'

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
    },
    # "Half-Life: Alyx"
    "546560": {"fsr_compatible": False},
    # "STAR WARS: Squadrons"
    "1222730": {"fsr_compatible": False},
    # "Automobilista 2"
    "1066890": {"fsr_compatible": False},
    # "Project CARS 2"
    "378860": {"fsr_compatible": False},
    # "DOOM VFR"
    "650000": {"fsr_compatible": False},
    # "Microsoft Flight Simulator"
    "1250410": {"fsr_compatible": False},
    # "PAYDAY 2"
    "218620": {"fsr_compatible": False},
    # "Euro Truck Simulator 2"
    "227300": {"fsr_compatible": True},
    # "American Truck Simulator"
    "270880": {"fsr_compatible": True},
    # "Radial-G : Racing Revolved"
    "330770": {"fsr_compatible": False},
    # "Creed: Rise to Glory"
    "804490": {"fsr_compatible": False},
    # "RaceRoom Racing Experience"
    "211500": {"fsr_compatible": False},
    # "Onward"
    "496240": {"fsr_compatible": False},
}

RF2_APPID = [k for k in KNOWN_APPS.keys()][0]

# Frozen or Debugger
if getattr(sys, 'frozen', False):
    # -- Running in PyInstaller Bundle ---
    FROZEN = True
else:
    # -- Running in IDE ---
    FROZEN = False

# Detect PyTest run
if any(re.findall(r'pytest|py.test', sys.argv[0])):
    PYTEST = True
else:
    PYTEST = False

_test_data_input_path = Path(__file__).parent.parent / 'tests' / 'data' / 'input'
_test_data_output_path = Path(__file__).parent.parent / 'tests' / 'data' / 'output'

if not PYTEST:
    SETTINGS_FILE_NAME = 'settings.json' if FROZEN else 'settings_dev.json'
else:
    SETTINGS_FILE_NAME = 'settings_tests.json'

if not PYTEST:
    APPS_STORE_FILE_NAME = 'steam_apps.json'
else:
    APPS_STORE_FILE_NAME = 'steam_apps_tests.json'

if not PYTEST:
    CUSTOM_APPS_STORE_FILE_NAME = '_apps.json'
else:
    CUSTOM_APPS_STORE_FILE_NAME = '_apps_tests.json'


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
    if PYTEST:
        return Path(check_and_create_dir(_test_data_output_path / 'settings_dir'))
    else:
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

    f = Path('.') / 'version.txt'
    try:
        with open(f.as_posix(), 'r') as f:
            version = f.read()
            return version
    except Exception as e:
        print('Duh!', e)

    return '0.0.0'


