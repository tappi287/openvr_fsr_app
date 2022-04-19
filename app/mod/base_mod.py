import logging
from pathlib import Path
from shutil import copyfile
from typing import Optional

import app.cfg
from app.cfg import BaseModCfgType, BaseModSettings
from app.mod import BaseModType, update_mod_data_dirs, get_mod_version_from_dll


class BaseMod:
    TYPE = BaseModType.invalid
    VAR_NAMES = {
        'installed': 'installed',
        'version': 'version',
        'settings': 'settings',
    }
    DLL_LOC_KEY_SELECTED = 'openVrDllPathsSelected'
    DLL_LOC_KEY = 'openVrDllPaths'
    DLL_NAME = app.globals.OPEN_VR_DLL

    def __init__(self, manifest, settings):
        """ Mod base class to handle installation/uninstallation
        
        :param dict manifest: The app's Steam manifest with additional settings dict
        :param BaseModSettings settings: Cfg settings handler
        """
        self.manifest = manifest
        self.settings = settings

        if self.VAR_NAMES['settings'] not in self.manifest:
            self.manifest[self.VAR_NAMES['settings']] = self.settings.to_js()

        self.engine_dll: Optional[Path] = None
        self._error_ls = list()

        # -- Verify paths are up-to-date after updates/game movement
        if not self.verify_engine_dll_selected_paths(self.manifest):
            self.reset_engine_dll_selected_paths(self.manifest)

    @property
    def error(self):
        return ' '.join(self._error_ls)

    @error.setter
    def error(self, value):
        self._error_ls.append(value)

    def reset_settings(self) -> bool:
        try:
            settings_class_name = type(self.settings).__name__
            settings_class = getattr(app.cfg, settings_class_name)
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
        if self.TYPE == BaseModType.invalid:
            logging.error('Tried to setup OpenVRMod from disk in base class! Use mod specific sub class instead!')
            return False

        cfg_results = list()
        for engine_dll in self._update_engine_dll_paths():
            if not engine_dll:
                continue

            # -- Write updated settings to disk
            if write:
                r = self.settings.write_cfg(self.engine_dll.parent, self.get_source_dir())
                cfg_results.append(r)
                if not r:
                    self.error = f'Error writing updated Settings CFG.'
                continue

            # -- Read settings from disk
            settings_read = self.settings.read_from_cfg(self.engine_dll.parent)
            cfg_results.append(settings_read)

            if settings_read:
                version = get_mod_version_from_dll(self.engine_dll, self.TYPE)
                self.manifest[self.VAR_NAMES['version']] = version or 'Unknown Version'
                self.manifest[self.VAR_NAMES['settings']] = self.settings.to_js()

        self.manifest[self.VAR_NAMES['installed']] = any(cfg_results)
        return all(cfg_results) if cfg_results else False

    def _update_cfg_single(self) -> bool:
        if not self.settings.write_cfg(self.engine_dll.parent, self.get_source_dir()):
            msg = 'Error writing OpenVRMod CFG file.'
            self.error = msg
            return False
        return True

    def _update_engine_dll_paths(self):
        # -- Merge e.g. multiple executables in the same directory
        dll_path_dirs = {Path(p).parent for p in self.manifest.get(self.DLL_LOC_KEY_SELECTED) or list()}

        for dll_path_dir in dll_path_dirs:
            if not dll_path_dir.exists():
                self.error = f'{self.DLL_NAME} not found in: ' + self.manifest.get('name')
                yield None

            engine_dll_path = dll_path_dir / self.DLL_NAME
            self.engine_dll = engine_dll_path
            yield engine_dll_path

    def uninstall(self) -> bool:
        return self.install(uninstall=True)

    def install(self, uninstall: bool = False) -> bool:
        results = list()
        for engine_dll in self._update_engine_dll_paths():
            if not engine_dll and self.TYPE != BaseModType.vrp:
                results.append(False)
                continue
            results.append(self._install_single(uninstall))

        if all(results):
            self.manifest[self.VAR_NAMES['installed']] = not uninstall

        return all(results)

    def _install_single(self, uninstall: bool = False) -> bool:
        org_engine_dll = self.engine_dll.parent / f'{self.engine_dll.stem}.orig{self.engine_dll.suffix}'

        try:
            # --- Installation
            if not uninstall:
                if self._install_mod(org_engine_dll):
                    return True

            # --- Uninstallation or Restore if installation failed
            self._uninstall_mod(org_engine_dll)
        except Exception as e:
            msg = f'Error during OpenVRMod install/uninstall: {e}'
            logging.error(msg)
            self.error = msg
            return False
        return True

    def _uninstall_mod(self, org_engine_dll: Path):
        # -- Restore original open_vr.dll
        if self.settings.CFG_TYPE == BaseModCfgType.open_vr_mod:
            legacy_dll_bak = self.engine_dll.with_suffix('.original')

            if org_engine_dll.exists() or legacy_dll_bak.exists():
                # Remove Fsr dll
                self.engine_dll.unlink(missing_ok=True)

                # Rename original open vr dll
                if org_engine_dll.exists():
                    org_engine_dll.rename(self.engine_dll)
                if legacy_dll_bak.exists():
                    legacy_dll_bak.rename(self.engine_dll)
        # -- Remove installed dxgi.dll
        elif self.settings.CFG_TYPE == BaseModCfgType.vrp_mod:
            self.engine_dll.unlink(True)

        # Remove Cfg
        if not self.settings.delete_cfg(self.engine_dll.parent):
            return False
        return True

    def _install_mod(self, org_engine_dll: Path):
        # Rename / Create backUp
        if not org_engine_dll.exists() and self.engine_dll.exists():
            self.engine_dll.rename(org_engine_dll)

        if self.engine_dll.exists():
            self.engine_dll.unlink()

        # Copy
        copyfile(self.get_source_dll(), self.engine_dll)

        if not self.settings.write_cfg(self.engine_dll.parent, self.get_source_dir()):
            self.error = 'Error writing Mod CFG file.'
            return False
        return True

    def get_version(self):
        results = list()
        for engine_dll in self._update_engine_dll_paths():
            if not engine_dll:
                continue

            try:
                results.append(get_mod_version_from_dll(self.engine_dll, self.TYPE))
            except Exception as e:
                msg = f'Error reading dll version: {e}'
                self.error = msg
                logging.error(msg)

        version = ''
        for result in results:
            if version and result != version:
                logging.warning('Found multiple installed Mod versions for the same app! %s',
                                self.manifest['appid'])
            version = result

        if not version:
            version = 'Unknown Version'

        self.manifest[self.VAR_NAMES['version']] = version
        return version

    def reset_engine_dll_selected_paths(self, manifest):
        manifest[self.DLL_LOC_KEY_SELECTED] = manifest.get(self.DLL_LOC_KEY, list()) or list()

    def verify_engine_dll_selected_paths(self, manifest) -> bool:
        """ Verify all selected paths still exist """
        results = list()
        for selected_engine_dll_path in manifest.get(self.DLL_LOC_KEY_SELECTED, list()) or list():
            results.append(selected_engine_dll_path in manifest.get(self.DLL_LOC_KEY))

        return all(results)

    def get_source_dir(self) -> Path:
        return Path(update_mod_data_dirs().get(self.TYPE))

    def get_source_dll(self) -> Path:
        return self.get_source_dir() / self.DLL_NAME
