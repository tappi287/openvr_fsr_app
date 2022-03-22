import json
import logging
from pathlib import Path

import app.globals as app_globals
from app.util.utils import JsonRepr


class AppSettings(JsonRepr):
    skip_keys = ['open_vr_fsr_versions', 'open_vr_foveated_versions', 'vrperfkit_versions',
                 'current_fsr_version', 'current_foveated_version', 'current_vrperfkit_version',
                 'SETTINGS_FILE_OVR']

    backup_created = False
    needs_admin = False
    previous_version = str()

    user_app_directories = {
        app_globals.USER_APP_PREFIX: app_globals.get_settings_dir().as_posix(),
    }

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
        'v0.3.0': '8bd81654a1a8cf77e7f7a54bb137c7ac',
    }
    current_fsr_version = 'v2.1.1'
    current_foveated_version = 'v0.2'
    current_vrperfkit_version = 'v0.3.0'

    # Default plugin paths
    mod_data_dirs = dict()

    SETTINGS_FILE_OVR = ''

    def __init__(self):
        self.needs_admin = AppSettings.needs_admin
        self.backup_created = AppSettings.backup_created

    @classmethod
    def _get_settings_file(cls) -> Path:
        override_path = None
        if cls.SETTINGS_FILE_OVR:
            override_path = Path(cls.SETTINGS_FILE_OVR)
        return override_path or app_globals.get_settings_dir() / app_globals.SETTINGS_FILE_NAME

    @staticmethod
    def _get_steam_apps_file() -> Path:
        return app_globals.get_settings_dir() / app_globals.APPS_STORE_FILE_NAME

    @staticmethod
    def _get_custom_dir_file(dir_id: str) -> Path:
        return app_globals.get_settings_dir() / f'{dir_id}{app_globals.CUSTOM_APPS_STORE_FILE_NAME}'

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

        # -- Convert str dict keys to int
        AppSettings.mod_data_dirs = {int(k): v for k, v in AppSettings.mod_data_dirs.items()}
        # -- Create UserApps fake dir
        if app_globals.USER_APP_PREFIX not in AppSettings.user_app_directories:
            AppSettings.user_app_directories.update({
                app_globals.USER_APP_PREFIX: app_globals.get_settings_dir().as_posix(),
            })
        return True

    @classmethod
    def extract_custom_apps(cls, steam_apps: dict) -> dict:
        # -- Setup custom apps dict
        custom_apps = dict()
        for dir_id in AppSettings.user_app_directories:
            custom_apps[dir_id] = dict()

        # -- Extract custom dir apps
        extract_ids = set()
        for app_id in steam_apps:
            for dir_id in AppSettings.user_app_directories:
                if app_id.startswith(dir_id):
                    extract_ids.add(app_id)
                    custom_apps[dir_id][app_id] = steam_apps.get(app_id)

        # -- Remove from steam_apps
        for app_id in extract_ids:
            steam_apps.pop(app_id)

        return custom_apps

    @classmethod
    def save_steam_apps(cls, steam_apps: dict) -> bool:
        # -- Save apps in custom app dirs
        custom_apps = cls.extract_custom_apps(steam_apps)
        for dir_id in AppSettings.user_app_directories:
            cls.save_custom_dir_apps(dir_id, custom_apps[dir_id])

        if not steam_apps:
            return True

        # -- Save steam apps
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
        # -- Add custom dir apps
        custom_apps = cls.load_custom_dir_apps()

        # -- Locate cached steam apps
        file = cls._get_steam_apps_file()
        if not file.exists():
            return custom_apps

        try:
            with open(file.as_posix(), 'r') as f:
                # noinspection PyTypeChecker
                steam_apps = json.load(f)
        except Exception as e:
            logging.error('Could not load steam apps from file! %s', e)
            return dict()

        # -- Add Known Apps data
        for app_id, entry in steam_apps.items():
            if app_id in app_globals.KNOWN_APPS:
                entry.update(app_globals.KNOWN_APPS[app_id])

        # -- Merge in custom apps
        steam_apps.update(custom_apps)

        return steam_apps

    @classmethod
    def save_custom_dir_apps(cls, dir_id, custom_apps) -> bool:
        file = cls._get_custom_dir_file(dir_id)

        try:
            with open(file.as_posix(), 'w') as f:
                # noinspection PyTypeChecker
                f.write(json.dumps(custom_apps))
        except Exception as e:
            logging.error('Could not store custom apps to file! %s', e)
            return False
        return True

    @classmethod
    def remove_custom_dir_apps(cls, dir_id) -> bool:
        file = cls._get_custom_dir_file(dir_id)

        try:
            file.unlink()
        except Exception as e:
            logging.error('Could not remove custom apps cache file! %s', e)
            return False
        return True

    @classmethod
    def load_custom_dir_apps(cls) -> dict:
        custom_apps = dict()

        for dir_id in AppSettings.user_app_directories:
            custom_apps[dir_id] = dict()
            file = cls._get_custom_dir_file(dir_id)
            if not file.exists():
                continue

            try:
                with open(file.as_posix(), 'r') as f:
                    # noinspection PyTypeChecker
                    custom_apps[dir_id] = json.load(f)
            except Exception as e:
                logging.error('Could not load custom apps from file! %s', e)
                return dict()

        result_apps = dict()
        for dir_id in custom_apps:
            result_apps.update(custom_apps[dir_id])

        for app_id in result_apps:
            result_apps[app_id]['userApp'] = True

        return result_apps
