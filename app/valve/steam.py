"""
    Utilities to read Valve's Steam Library on a Windows Machine
"""
import logging
import winreg as registry
from pathlib import Path, WindowsPath
from typing import Iterable, List, Optional, Tuple

from . import acf
from app.globals import KNOWN_APPS
from app.util.utils import convert_unit, SizeUnit

STEAM_LIBRARY_FOLDERS = 'LibraryFolders'
STEAM_LIBRARY_FILE = 'libraryfolders.vdf'
STEAM_APPS_FOLDER = 'steamapps'
STEAM_APPS_INSTALL_FOLDER = 'common'


class SteamApps:
    STEAM_LOCATION = Path('.')

    def __init__(self):
        self.steam_apps, self.known_apps = dict(), dict()
        self.steam_app_names = {m.get('name'): app_id for app_id, m in self.steam_apps.items() if isinstance(m, dict)}
        detected_steam_location = self.find_steam_location()

        if detected_steam_location:
            SteamApps.STEAM_LOCATION = Path(detected_steam_location)

    @staticmethod
    def find_steam_location() -> Optional[str]:
        try:
            key = registry.OpenKey(registry.HKEY_CURRENT_USER, "Software\Valve\Steam")
        except FileNotFoundError as e:
            logging.error(e)
            return None

        return registry.QueryValueEx(key, "SteamPath")[0]

    def read_steam_library(self):
        self.steam_apps, self.known_apps = self.find_installed_steam_games()

    def find_game_location(self, app_id: int = 0, app_name: str = '') -> Optional[Path]:
        """ Shorthand method to search installed apps via either id or name """
        if app_name:
            name_hits = [n for n in self.steam_app_names.keys() if n.startswith(app_name)]
            if name_hits:
                app_id = self.steam_app_names.get(name_hits[0])

        if app_id is None or app_id == 0:
            return

        m = self.steam_apps.get(app_id)
        if not m:
            logging.error('Could not locate Steam app with id %s', app_id)
            return

        for lib_folder in self.steam_apps.get(STEAM_LIBRARY_FOLDERS, list()):
            app_folder = lib_folder / STEAM_APPS_INSTALL_FOLDER / m.get('installdir')

            if app_folder.exists():
                return app_folder

    @staticmethod
    def find_steam_libraries() -> Optional[List[Path]]:
        """ Return Steam Library Path's as pathlib.Path objects """
        steam_apps_dir = SteamApps.STEAM_LOCATION / STEAM_APPS_FOLDER
        steam_lib_file = steam_apps_dir / STEAM_LIBRARY_FILE
        if not steam_lib_file.exists():
            return [steam_apps_dir]

        lib_data, lib_folders = dict(), [steam_apps_dir]
        try:
            with open(steam_lib_file.as_posix(), 'r') as f:
                lib_data = acf.load(f)
        except Exception as e:
            logging.error(f'Could not read Steam Library {steam_lib_file.name} file: {e}')

        # "LibraryFolders" => "libraryfolders"
        if STEAM_LIBRARY_FOLDERS.casefold() in lib_data:
            lib_data[STEAM_LIBRARY_FOLDERS] = lib_data.get(STEAM_LIBRARY_FOLDERS.casefold())

        for k, v in lib_data.get(STEAM_LIBRARY_FOLDERS, dict()).items():
            if isinstance(k, str) and k.isdigit():
                if isinstance(v, str):
                    lib_dir = Path(v) / STEAM_APPS_FOLDER
                    if lib_dir.exists():
                        lib_folders.append(lib_dir)
                elif isinstance(v, dict):
                    lib_dir = Path(v.get('path')) / STEAM_APPS_FOLDER
                    if lib_dir.exists():
                        lib_folders.append(lib_dir)

        return lib_folders

    @staticmethod
    def _add_path(manifest: dict, lib_folders):
        """ Create an 'path' key with an absolute path to the installation directory """
        p = manifest.get('installdir')
        manifest['path'] = ''

        for lib_folder in lib_folders:
            if not p:
                break
            abs_p = lib_folder / STEAM_APPS_INSTALL_FOLDER / p
            if not abs_p.exists():
                continue

            manifest['installdir'] = abs_p.as_posix()

            # Update absolute path to executable
            if manifest.get('exe_sub_path'):
                # Remove potential leading slashes
                if manifest['exe_sub_path'][0] in ('/', '\\'):
                    manifest['exe_sub_path'] = manifest['exe_sub_path'][1:]
                manifest['path'] = Path(abs_p / manifest['exe_sub_path']).as_posix()
            else:
                manifest['path'] = abs_p.as_posix()

    def find_installed_steam_games(self) -> Tuple[dict, dict]:
        steam_apps, _known_apps = dict(), KNOWN_APPS
        lib_folders = self.find_steam_libraries()
        if not lib_folders:
            return steam_apps, _known_apps

        for lib in lib_folders:
            for manifest_file in lib.glob('appmanifest*.acf'):
                try:
                    with open(manifest_file.as_posix(), 'r', encoding='utf-8') as f:
                        manifest = acf.load(f)
                        if manifest is not None:
                            manifest = manifest.get('AppState')

                            # -- Skip invalid manifests
                            if manifest is None:
                                logging.warning('Skipping invalid App entry: %s', manifest_file.as_posix())
                                continue

                            # -- Add human readable size
                            manifest['sizeGb'] = f"{convert_unit(manifest.get('SizeOnDisk', 0), SizeUnit.GB):.1f} GB"

                            # -- Add Path information
                            self._add_path(manifest, lib_folders)

                            # -- Add known apps entries data
                            app_id = manifest.get('appid')

                            # -- Skip invalid IDs
                            if app_id is None:
                                logging.warning('Skipping App entry without id: %s', manifest_file.as_posix())
                                continue

                            if app_id in _known_apps:
                                for k, v in _known_apps[app_id].items():
                                    manifest[k] = v

                            # -- Store Entry
                            steam_apps[app_id] = manifest
                except Exception as e:
                    logging.error('Error reading Steam App manifest: %s %s', manifest_file, e)

        for app_id, entry_dict in _known_apps.items():
            if app_id in steam_apps:
                _known_apps[app_id].update(steam_apps[app_id])

            # -- Get install dir with special method for eg. CrewChief non steam app
            if 'simmon_method' in entry_dict.keys():
                method = getattr(KnownAppsMethods, entry_dict.get('simmon_method'))
                args = entry_dict.get('simmon_method_args')

                if callable(method):
                    entry_dict['installdir'] = method(*args)
                    if entry_dict['installdir'] is not None:
                        try:
                            install_dir = Path(entry_dict['installdir'])
                            if not install_dir.is_dir():
                                install_dir = install_dir.parent
                            entry_dict['installdir'] = str(WindowsPath(install_dir))
                            entry_dict['path'] = Path(install_dir / entry_dict['exe_sub_path']).as_posix()
                        except Exception as e:
                            logging.error('Error locating installation path: %s', e)
                    else:
                        entry_dict['path'] = ''

            # -- Update install dir to an absolute path if not already absolute
            self._add_path(entry_dict, lib_folders)

        steam_apps[STEAM_LIBRARY_FOLDERS] = lib_folders
        return steam_apps, _known_apps


class KnownAppsMethods:
    @classmethod
    def find_by_registry_keys_current_user(cls, *args):
        return cls.find_by_registry_keys(*args, user_reg=True)

    @staticmethod
    def find_by_registry_keys(keys: Iterable, key_name: Optional[str], user_reg: bool = False) -> Optional[str]:
        key = None
        reg = registry.HKEY_CURRENT_USER if user_reg else registry.HKEY_LOCAL_MACHINE

        for key_url in keys:
            try:
                key = registry.OpenKey(reg, key_url)
                break
            except FileNotFoundError as e:
                logging.error('Could not locate registry key %s: %s', key_url, e)

        if not key:
            return None

        try:
            value = registry.QueryValueEx(key, key_name)[0]

            # -- Remove quotes
            value = value.replace('"', '')

            # -- Remove parameters/arguments %1 %2
            while "%" in value:
                value = value.rsplit(' ', 1)[0]

            return value
        except FileNotFoundError as e:
            logging.error('Could not locate value in key %s: %s', key_name, e)


apps = SteamApps()
