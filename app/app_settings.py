import json
import logging
from pathlib import Path, WindowsPath
from typing import Optional, Union

from app.globals import get_settings_dir, SETTINGS_FILE_NAME, OPEN_VR_DLL, get_data_dir, APPS_STORE_FILE_NAME, KNOWN_APPS
from app.util.utils import JsonRepr


class AppSettings(JsonRepr):
    skip_keys = ['open_vr_fsr_versions', 'open_vr_foveated_versions', 'vrperfkit_versions'
                 'current_fsr_version', 'current_foveated_version', 'current_vrperfkit_version']

    backup_created = False
    needs_admin = False
    previous_version = str()
    user_apps = dict()
    user_app_counter = len(user_apps.keys())

    open_vr_fsr_versions = {
        'v0.5': 'd74d3083e3506d83fac0d95520625eab',
        'v0.6': '18c46267b042cac7c21a2059786e660c',
        'v0.7': 'f3a0706ea3929234a73bdfde58493601',
        'v0.8': '68fcb526c619103e4d9775e4fba2b747',
        'v0.9': 'ddccc71f8239bf17ead5df1db43eeedb',
        'v1.0': 'da03ca34b51587addebd78422f4d5c39',
        'v1.1': '628a13f0faae439229237c3b44e5426c',
        'v1.2': '2d551d67a642d3edba3e8467b00667cb',
        'v1.3': 'ea417d2480b9a285ea9f6a3e9aa703b3',
        'v2.0': 'b173ef3e95283c47f840152786d6ebf9',
        'v2.1.1': '1f15031338f117ccc8d68a98f71d6b65',
    }
    open_vr_foveated_versions = {
        'v0.1': 'f113aa2bbc9e13603fdc99c3944fcc48',
        'v0.2': '51bec8ad9c6860615a71c2449feee780'
    }
    vrperfkit_versions = {
        'v0.1': '161e5a771afe5f24c99592c9d4f95c30',
        'v0.1.1': '0559a8e6a1fc0021f9d5fb4d1cd9cc00',
        'v0.1.2': 'caed41dd77a7f5873f00215e67dded31',
        'v0.2': '017212ff2fabff1178462bf32923a6ce',
        'v0.2.1': '2baca682f41b5046f3245d200b4e3c02',
        'v0.2.2': '30531b66aa251f7ee7cfbc9b005d10b3',
    }
    current_fsr_version = 'v2.1.1'
    current_foveated_version = 'v0.2'
    current_vrperfkit_version = 'v0.2.2'

    # Default plugin path
    openvr_fsr_dir: Optional[str] = str(WindowsPath(get_data_dir() / 'openvr_fsr'))
    openvr_foveated_dir: Optional[str] = str(WindowsPath(get_data_dir() / 'openvr_foveated'))
    vrperfkit_dir: Optional[str] = str(WindowsPath(get_data_dir() / 'vrperfkit'))

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
