import json
import logging
from pathlib import Path, WindowsPath
from typing import Optional, Union

from .globals import get_settings_dir, SETTINGS_FILE_NAME, OPEN_VR_DLL, get_data_dir, APPS_STORE_FILE_NAME, get_version, KNOWN_APPS
from .utils import JsonRepr


class AppSettings(JsonRepr):
    backup_created = False
    needs_admin = False
    previous_version = str()

    # Default plugin path
    openvr_fsr_dir: Optional[str] = str(WindowsPath(get_data_dir() / 'openvr_fsr'))

    def __init__(self):
        self.needs_admin = AppSettings.needs_admin
        self.backup_created = AppSettings.backup_created

    @staticmethod
    def _get_settings_file() -> Path:
        return get_settings_dir() / SETTINGS_FILE_NAME

    @staticmethod
    def _get_steam_apps_file() -> Path:
        return get_settings_dir() / APPS_STORE_FILE_NAME

    @classmethod
    def save(cls):
        file = cls._get_settings_file()

        try:
            with open(file.as_posix(), 'w') as f:
                # noinspection PyTypeChecker
                f.write(json.dumps(cls.to_js_object(cls)))
        except Exception as e:
            logging.error('Could not save application settings! %s', e)
            return False
        return True

    @classmethod
    def load(cls) -> bool:
        file = cls._get_settings_file()

        try:
            if file.exists():
                with open(file.as_posix(), 'r') as f:
                    # -- Load Settings
                    # noinspection PyTypeChecker
                    cls.from_js_dict(cls, json.loads(f.read()))
        except Exception as e:
            logging.error('Could not load application settings! %s', e)
            return False

        return True

    @classmethod
    def save_steam_apps(cls, steam_apps: dict):
        file = cls._get_steam_apps_file()

        try:
            with open(file.as_posix(), 'w') as f:
                # noinspection PyTypeChecker
                f.write(json.dumps(steam_apps))
        except Exception as e:
            logging.error('Could not store steam apps to file! %s', e)
            return False
        return True

    @classmethod
    def load_steam_apps(cls) -> dict:
        file = cls._get_steam_apps_file()
        if not file.exists():
            return dict()

        # -- Re-create disk cache between versions
        if get_version() != cls.previous_version:
            return dict()

        try:
            with open(file.as_posix(), 'r') as f:
                # noinspection PyTypeChecker
                steam_apps = json.load(f)
        except Exception as e:
            logging.error('Could not load steam apps from file! %s', e)
            return dict()

        # -- Add Known Apps data
        for app_id, entry in steam_apps.items():
            if app_id in KNOWN_APPS:
                entry.update(KNOWN_APPS[app_id])

        return steam_apps

    @staticmethod
    def update_fsr_dir(fsr_plugin_dir: Union[str, Path]) -> bool:
        fsr_plugin_dir = Path(fsr_plugin_dir)
        dir_str = str(WindowsPath(fsr_plugin_dir))

        try:
            if fsr_plugin_dir.exists():
                verified = False
                for _ in fsr_plugin_dir.glob(OPEN_VR_DLL):
                    verified = True
                    break
                if not verified:
                    logging.error('Could not find OpenVR Api Dll in provided directory!')
                    return False
                logging.info('Updating FSR PlugIn Dir: %s', dir_str)
                AppSettings.openvr_fsr_dir = dir_str
                AppSettings.save()
            else:
                logging.error('Selected Presets Directory does not exist: %s', fsr_plugin_dir.as_posix())
                return False
        except Exception as e:
            logging.error('Error accessing path: %s', e)
            return False
        return True
