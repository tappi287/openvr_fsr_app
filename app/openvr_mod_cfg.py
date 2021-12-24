import json
import logging
from pathlib import Path
from typing import List

from app.globals import OPEN_VR_FSR_CFG
from app.utils import JsonRepr


class OpenVRModCfgSetting(JsonRepr):
    export_skip_keys = ['settings']

    def __init__(self, key=None, name=None, value=None, settings=None):
        self.key = key
        self.name = name
        self.value = value
        self.settings = settings


class OpenVRModSettings(JsonRepr):
    def __init__(self, options: List[OpenVRModCfgSetting], cfg_key: str):
        """ OpenVR Mod cfg base class to handle settings in openvr_mod.cfg configurations.

        :param options:
        :param cfg_key:
        """
        self.options = options
        self.cfg_key = cfg_key

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
                    json_value = json_dict[self.cfg_key].get(s.key)
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
                json.dump({self.cfg_key: {s.key: s.value for s in self._get_options()}}, f, indent=2)
            logging.info('Written updated config at: %s', plugin_path)
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
