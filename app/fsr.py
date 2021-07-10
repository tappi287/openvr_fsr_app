import json
import logging
from pathlib import Path
from shutil import copyfile
from typing import Optional

from app.app_settings import AppSettings
from app.globals import OPEN_VR_DLL, OPEN_VR_FSR_CFG
from app.utils import JsonRepr


class FsrSetting(JsonRepr):
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
            value=0.75,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.sharpness = FsrSetting(
            key='sharpness',
            name='Sharpness',
            value=0.75,
            settings=[{'settingType': 'range', 'min': 0.10, 'max': 3.0, 'step': 0.01, 'display': 'floatpercent'}]
        )
        self.options = [self.enabled.key, self.renderScale.key, self.sharpness.key]

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
                    s.value = json_dict['fsr'].get(s.key)
        except Exception as e:
            logging.error('Error reading FSR settings from cfg file: %s', e)
            return False
        return True

    def write_cfg(self, plugin_path) -> bool:
        cfg = plugin_path / OPEN_VR_FSR_CFG

        try:
            with open(cfg, 'w') as f:
                json.dump({'fsr': {s.key: s.value for s in self._get_options()}}, f, indent=2)
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
        except Exception as e:
            logging.error('Error deleting FSR settings cfg file: %s', e)
            return False
        return True

    def to_js(self) -> list:
        return [s.to_js_object() for s in self._get_options()]

    def from_js_dict(self, json_list):
        for s in json_list:
            setting = FsrSetting()
            setting.from_js_dict(s)
            setattr(self, setting.key, setting)


class Fsr:
    back_up_suffix = '.original'

    def __init__(self, manifest: dict):
        self.manifest = manifest

        self.settings = FsrSettings()
        self.settings.from_js_dict(manifest.get('settings'))

        self.open_vr_dll: Optional[Path] = None
        self.error = str()

    def _update_open_vr_dll_path(self):
        open_vr_dll = self.manifest.get('openVrDllPath')
        if not open_vr_dll:
            self.error = 'Open VR Api Dll not found in: ' + self.manifest.get('name')
            return False

        self.open_vr_dll = Path(open_vr_dll)
        return True

    def update_cfg(self) -> bool:
        if not self._update_open_vr_dll_path():
            return False
        if not self.settings.write_cfg(self.open_vr_dll.parent):
            msg = 'Error writing Fsr cfg file.'
            self.error = msg
            return False
        return True

    def uninstall(self) -> bool:
        return self.install(True)

    def install(self, uninstall: bool = False) -> bool:
        if not self._update_open_vr_dll_path():
            return False

        org_open_vr_dll = self.open_vr_dll.with_suffix(self.back_up_suffix)

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
        if org_open_vr_dll.exists():
            # Remove Fsr dll
            self.open_vr_dll.unlink()
            # Rename original open vr dll
            org_open_vr_dll.rename(self.open_vr_dll)

        # Remove Cfg
        if not self.settings.delete_cfg(self.open_vr_dll.parent):
            return False
        return True

    def _install_fsr(self, org_open_vr_dll: Path):
        fsr_open_vr_dll = Path(AppSettings.openvr_fsr_dir) / OPEN_VR_DLL

        # Rename / Create backUp
        if not org_open_vr_dll.exists():
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
