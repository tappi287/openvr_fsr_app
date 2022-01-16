import logging
from pathlib import Path
from shutil import copyfile
from typing import Optional, Iterable

import app
from app.app_settings import AppSettings
from app.utils import get_file_hash


class OpenVRModType:
    invalid = -1
    fsr = 0
    foveated = 1

    mod_types = {0: 'FsrMod', 1: 'FoveatedMod'}


class OpenVRMod:
    TYPE = OpenVRModType.invalid
    VAR_NAMES = {
        'installed': 'installed',
        'version': 'version',
        'settings': 'settings',
    }

    def __init__(self, manifest, settings, mod_dll_location):
        """ Open VR Mod base class to handle installation/uninstallation
        
        :param dict manifest: The app's Steam manifest with additional settings dict
        :param app.openvr_mod_cfg.OpenVRModSettings settings: Cfg settings handler
        :param Path mod_dll_location: Path to the OpenVRMod dll to install
        """
        self.manifest = manifest
        self.settings = settings

        if self.VAR_NAMES['settings'] not in self.manifest:
            self.manifest[self.VAR_NAMES['settings']] = self.settings.to_js()

        self.open_vr_dll: Optional[Path] = None
        self.mod_dll_location = mod_dll_location
        self._error_ls = list()

        # -- Verify paths are up-to-date after updates/game movement
        if not self.verify_open_vr_selected_paths(self.manifest):
            self.reset_open_vr_selected_paths(self.manifest)

    @property
    def error(self):
        return ' '.join(self._error_ls)

    @error.setter
    def error(self, value):
        self._error_ls.append(value)

    def reset_settings(self) -> bool:
        try:
            settings_class_name = type(self.settings).__name__
            settings_class = getattr(app, settings_class_name)
            self.settings = settings_class()
            self.manifest[self.VAR_NAMES['settings']] = self.settings.to_js()
        except Exception as e:
            msg = f'Could not reset Mod settings: {e}'
            logging.error(msg)
            self.error = msg
            return False
        return True

    def write_updated_cfg(self) -> bool:
        return self._read_write_cfg(True)

    def update_from_disk(self) -> bool:
        return self._read_write_cfg(False)

    def _read_write_cfg(self, write: bool = False):
        if self.TYPE == OpenVRModType.invalid:
            logging.error('Tried to setup OpenVRMod from disk in base class! Use mod specific sub class instead!')
            return False

        cfg_results = list()
        for open_vr_dll in self.manifest.get('openVrDllPathsSelected'):
            if not self._update_open_vr_dll_path(open_vr_dll):
                continue

            if write:
                # -- Write updated settings to disk
                r = self.settings.write_cfg(self.open_vr_dll.parent)
                cfg_results.append(r)
                continue

            # -- Read settings from disk
            settings_read = self.settings.read_from_cfg(self.open_vr_dll.parent)
            cfg_results.append(settings_read)

            if settings_read:
                version = self.get_mod_version_from_dll(self.open_vr_dll, self.TYPE)
                self.manifest[self.VAR_NAMES['version']] = version or 'Unknown Version'
                self.manifest[self.VAR_NAMES['settings']] = self.settings.to_js()

        self.manifest[self.VAR_NAMES['installed']] = any(cfg_results)
        return True

    def _update_cfg_single(self) -> bool:
        if not self.settings.write_cfg(self.open_vr_dll.parent):
            msg = 'Error writing OpenVRMod CFG file.'
            self.error = msg
            return False
        return True

    def _update_open_vr_dll_path(self, open_vr_dll: str):
        if not open_vr_dll:
            self.error = 'Open VR Api Dll not found in: ' + self.manifest.get('name')
            return False

        open_vr_dll = Path(open_vr_dll)
        self.open_vr_dll = open_vr_dll
        return True

    def uninstall(self) -> bool:
        return self.install(uninstall=True)

    def install(self, uninstall: bool = False) -> bool:
        results = list()
        for open_vr_dll in self.manifest.get('openVrDllPathsSelected'):
            if not self._update_open_vr_dll_path(open_vr_dll):
                results.append(False)
                continue
            results.append(self._install_single(uninstall))

        if all(results):
            self.manifest[self.VAR_NAMES['installed']] = not uninstall

        return all(results)

    def _install_single(self, uninstall: bool = False) -> bool:
        org_open_vr_dll = self.open_vr_dll.parent / f'{self.open_vr_dll.stem}.orig{self.open_vr_dll.suffix}'

        try:
            # --- Installation
            if not uninstall:
                if self._install_mod(org_open_vr_dll):
                    return True

            # --- Uninstallation or Restore if installation failed
            self._uninstall_fsr(org_open_vr_dll)
        except Exception as e:
            msg = f'Error during OpenVRMod install/uninstall: {e}'
            logging.error(msg)
            self.error = msg
            return False
        return True

    def _uninstall_fsr(self, org_open_vr_dll: Path):
        legacy_dll_bak = self.open_vr_dll.with_suffix('.original')

        if org_open_vr_dll.exists() or legacy_dll_bak.exists():
            # Remove Fsr dll
            self.open_vr_dll.unlink(missing_ok=True)

            # Rename original open vr dll
            if org_open_vr_dll.exists():
                org_open_vr_dll.rename(self.open_vr_dll)
            if legacy_dll_bak.exists():
                legacy_dll_bak.rename(self.open_vr_dll)

        # Remove Cfg
        if not self.settings.delete_cfg(self.open_vr_dll.parent):
            return False
        return True

    def _install_mod(self, org_open_vr_dll: Path):
        # Rename / Create backUp
        if not org_open_vr_dll.exists() and self.open_vr_dll.exists():
            self.open_vr_dll.rename(org_open_vr_dll)

        if self.open_vr_dll.exists():
            self.open_vr_dll.unlink()

        # Copy
        copyfile(self.mod_dll_location, self.open_vr_dll)

        if not self.settings.write_cfg(self.open_vr_dll.parent):
            self.error = 'Error writing OpenVR-Mod CFG file.'
            return False
        return True

    @staticmethod
    def get_mod_version_from_dll(openvr_dll: Path, mod_type: int) -> Optional[str]:
        file_hash = get_file_hash(openvr_dll.as_posix())
        version_dict = dict()

        if mod_type == OpenVRModType.fsr:
            version_dict = AppSettings.open_vr_fsr_versions
        elif mod_type == OpenVRModType.foveated:
            version_dict = AppSettings.open_vr_foveated_versions

        for version, hash_str in version_dict.items():
            if file_hash != hash_str:
                continue
            return version

    def get_version(self):
        results = list()
        for open_vr_dll in self.manifest.get('openVrDllPathsSelected'):
            if not self._update_open_vr_dll_path(open_vr_dll):
                continue
            try:
                results.append(self.get_mod_version_from_dll(self.open_vr_dll, self.TYPE))
            except Exception as e:
                msg = f'Error reading dll version: {e}'
                self.error = msg
                logging.error(msg)

        version = ''
        for result in results:
            if version and result != version:
                logging.warning('Found multiple installed OpenVR FSR versions for the same app! %s',
                                self.manifest['appid'])
            version = result

        if not version:
            version = 'Unknown Version'

        self.manifest[self.VAR_NAMES['version']] = version
        return version

    @staticmethod
    def reset_open_vr_selected_paths(manifest):
        manifest['openVrDllPathsSelected'] = manifest.get('openVrDllPaths')

    @staticmethod
    def verify_open_vr_selected_paths(manifest) -> bool:
        """ Verify all selected paths still exist """
        results = list()
        for open_vr_selected_path in manifest.get('openVrDllPathsSelected'):
            results.append(
                open_vr_selected_path in manifest.get('openVrDllPaths')
            )
        return all(results)


def get_mod(manifest: dict, mod_type: int = 0) -> OpenVRMod:
    mod_type_class = getattr(app, OpenVRModType.mod_types.get(mod_type))
    return mod_type_class(manifest)


def get_available_mods(manifest: dict) -> Iterable[OpenVRMod]:
    for mod_type in OpenVRModType.mod_types.keys():
        yield get_mod(manifest, mod_type)
