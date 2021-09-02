import json
import logging
from pathlib import Path
from shutil import copyfile
from typing import Optional

from app.app_settings import AppSettings
from app.globals import OPEN_VR_DLL, OPEN_VR_FSR_CFG
from app.utils import JsonRepr


def reduce_steam_apps_for_export(steam_apps) -> dict:
    reduced_dict = dict()

    for app_id, entry in steam_apps.items():
        fsr = Fsr(entry)

        reduced_dict[app_id] = dict()
        # Add only necessary data
        reduced_dict[app_id]['settings'] = fsr.settings.to_js(export=True)
        reduced_dict[app_id]['fsrInstalled'] = entry.get('fsrInstalled')
        reduced_dict[app_id]['fsr_compatible'] = entry.get('fsr_compatible', True)
        reduced_dict[app_id]['name'] = entry.get('name')
        reduced_dict[app_id]['sizeGb'] = entry.get('sizeGb')
        reduced_dict[app_id]['path'] = entry.get('path')
        reduced_dict[app_id]['openVrDllPaths'] = entry.get('openVrDllPaths')
        reduced_dict[app_id]['openVrDllPathsSelected'] = entry.get('openVrDllPathsSelected')
        reduced_dict[app_id]['openVr'] = entry.get('openVr')
        reduced_dict[app_id]['SizeOnDisk'] = entry.get('SizeOnDisk')
        reduced_dict[app_id]['appid'] = entry.get('appid')

    return reduced_dict


class FsrSetting(JsonRepr):
    export_skip_keys = ['settings']

    def __init__(self, key=None, name=None, value=None, settings=None):
        self.key = key
        self.name = name
        self.value = value
        self.settings = settings


class FsrSettings(JsonRepr):
    def __init__(self):
        self.enabled = FsrSetting(
            key='enabled',
            name='Enabled',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.renderScale = FsrSetting(
            key='renderScale',
            name='Render Scale',
            value=0.77,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.sharpness = FsrSetting(
            key='sharpness',
            name='Sharpness',
            value=0.75,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.radius = FsrSetting(
            key='radius',
            name='Radius',
            value=0.50,
            settings=[{'settingType': 'range', 'min': 0.20, 'max': 2.00, 'step': 0.01}]
        )
        self.applyMIPBias = FsrSetting(
            key='applyMIPBias',
            name='Apply MIP Bias',
            value=True,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.debugMode = FsrSetting(
            key='debugMode',
            name='Debug Mode',
            value=False,
            settings=[{'value': True, 'name': 'On'}, {'value': False, 'name': 'Off'}]
        )
        self.options = [self.enabled.key, self.renderScale.key, self.sharpness.key, self.radius.key,
                        self.applyMIPBias.key, self.debugMode.key]

    def _get_options(self):
        for key in self.options:
            yield getattr(self, key)

    def read_from_cfg(self, plugin_path: Path) -> bool:
        cfg = plugin_path / OPEN_VR_FSR_CFG
        if not cfg.exists():
            return False

        try:
            with open(cfg, 'r') as f:
                # -- Remove Inline Comments
                json_str = str()
                for line in f.readlines():
                    if '//' not in line and '#' not in line:
                        json_str += line

                json_dict = json.loads(json_str)
                for s in self._get_options():
                    json_value = json_dict['fsr'].get(s.key)
                    if json_value is not None:
                        s.value = json_value
        except Exception as e:
            logging.error('Error reading FSR settings from cfg file: %s', e)
            return False
        return True

    def write_cfg(self, plugin_path) -> bool:
        cfg = plugin_path / OPEN_VR_FSR_CFG

        try:
            with open(cfg, 'w') as f:
                json.dump({'fsr': {s.key: s.value for s in self._get_options()}}, f, indent=2)
            logging.info('Updated config at: %s', plugin_path)
        except Exception as e:
            logging.error('Error writing FSR settings to cfg file: %s', e)
            return False
        return True

    @staticmethod
    def delete_cfg(plugin_path) -> bool:
        cfg = plugin_path / OPEN_VR_FSR_CFG
        if not cfg.exists():
            return True

        try:
            cfg.unlink()
            logging.info('Deleted config at: %s', plugin_path)
        except Exception as e:
            logging.error('Error deleting FSR settings cfg file: %s', e)
            return False
        return True

    def to_js(self, export: bool = False) -> list:
        return [s.to_js_object(export) for s in self._get_options()]

    def from_js_dict(self, json_list):
        for s in json_list:
            for setting in self._get_options():
                if setting.key == s.get('key'):
                    setting.value = s.get('value')


class Fsr:
    def __init__(self, manifest: dict):
        self.manifest = manifest

        self.settings = FsrSettings()
        self.settings.from_js_dict(manifest.get('settings'))

        self.open_vr_dll: Optional[Path] = None
        self.extra_fsr_path = manifest.get('fsr_install_dir')
        self._error_ls = list()

    @property
    def error(self):
        return ' '.join(self._error_ls)

    @error.setter
    def error(self, value):
        self._error_ls.append(value)

    def update_cfg(self) -> bool:
        results = list()
        for open_vr_dll in self.manifest.get('openVrDllPathsSelected'):
            if not self._update_open_vr_dll_path(open_vr_dll):
                results.append(False)
                continue
            results.append(self._update_cfg_single())

        return all(results)

    def _update_cfg_single(self) -> bool:
        if not self.settings.write_cfg(self.open_vr_dll.parent):
            msg = 'Error writing Fsr cfg file.'
            self.error = msg
            return False
        return True

    def _update_open_vr_dll_path(self, open_vr_dll: str):
        if not open_vr_dll:
            self.error = 'Open VR Api Dll not found in: ' + self.manifest.get('name')
            return False

        open_vr_dll = Path(open_vr_dll)
        self.open_vr_dll = open_vr_dll

        # -- Adjust install path for known exceptions
        if self.extra_fsr_path:
            self.open_vr_dll = open_vr_dll.parent / self.extra_fsr_path / open_vr_dll.name
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

        return all(results)

    def _install_single(self, uninstall: bool = False) -> bool:
        org_open_vr_dll = self.open_vr_dll.parent / f'{self.open_vr_dll.stem}.orig{self.open_vr_dll.suffix}'

        try:
            # --- Installation
            if not uninstall:
                if self._install_fsr(org_open_vr_dll):
                    return True

            # --- Uninstallation or Restore if installation failed
            self._uninstall_fsr(org_open_vr_dll)
        except Exception as e:
            msg = f'Error during fsr install/uninstall: {e}'
            logging.error(msg)
            self.error = msg
            return False
        return True

    def _uninstall_fsr(self, org_open_vr_dll: Path):
        legacy_dll_bak = self.open_vr_dll.with_suffix('.original')

        if org_open_vr_dll.exists() or legacy_dll_bak.exists():
            # Remove Fsr dll
            self.open_vr_dll.unlink()
            # Rename original open vr dll
            if org_open_vr_dll.exists():
                org_open_vr_dll.rename(self.open_vr_dll)
            if legacy_dll_bak.exists():
                legacy_dll_bak.rename(self.open_vr_dll)

        # Remove Cfg
        if not self.settings.delete_cfg(self.open_vr_dll.parent):
            return False
        return True

    def _install_fsr(self, org_open_vr_dll: Path):
        fsr_open_vr_dll = Path(AppSettings.openvr_fsr_dir) / OPEN_VR_DLL

        # Rename / Create backUp
        if not org_open_vr_dll.exists() and self.open_vr_dll.exists():
            self.open_vr_dll.rename(org_open_vr_dll)

        if self.open_vr_dll.exists():
            self.open_vr_dll.unlink()

        # Copy
        copyfile(fsr_open_vr_dll, self.open_vr_dll)

        if not self.settings.write_cfg(self.open_vr_dll.parent):
            msg = 'Error writing Fsr cfg file.'
            self.error = msg
            return False
        return True
