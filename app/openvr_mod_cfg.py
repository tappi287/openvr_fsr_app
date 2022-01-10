import json
import logging
from pathlib import Path
from typing import List

from app.globals import OPEN_VR_FSR_CFG
from app.utils import JsonRepr


class OpenVRModCfgSetting(JsonRepr):
    export_skip_keys = ['settings', 'category']
    is_openvr_mod_cfg_setting = True

    def __init__(self, key=None, name=None, value=None, desc=None,
                 keyName=None, settings=None, parent=None, category=None, hidden=False):
        self.key = key
        self.name = name
        self.desc = desc
        self.value = value
        self.keyName = keyName
        self.settings = settings
        self.parent = parent
        self.category = category
        self.hidden = hidden


class OpenVRModSettings(JsonRepr):
    def __init__(self, options: List[str], cfg_key: str):
        """ OpenVR Mod cfg base class to handle settings in openvr_mod.cfg configurations.

        :param options:
        :param cfg_key:
        """
        self.options = options
        self.cfg_key = cfg_key

    def get_setting_fields(self):
        options = list()
        for attr_name in dir(self):
            field = getattr(self, attr_name)
            if hasattr(field, 'is_openvr_mod_cfg_setting'):
                options.append(attr_name)
        return options

    def _get_options(self):
        for key in self.options:
            option = getattr(self, key)
            if not option.parent:
                yield option

    def _get_all_options(self):
        for key in self.options:
            yield getattr(self, key)

    def _get_option_by_key(self, key, parent_key=None):
        for option in self._get_all_options():
            if option.parent == parent_key and key == option.key:
                return option

    def _get_parented_options(self) -> dict:
        parented_options = dict()
        for o in self._get_all_options():
            if o.parent:
                parent_option = self._get_option_by_key(o.parent)
                if parent_option.key not in parented_options:
                    parented_options[parent_option.key] = dict()
                parented_options[parent_option.key][o.key] = o.value

        return parented_options

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

                # -- Check if the cfg key e.g. 'fsr' is defined inside the CFG
                if self.cfg_key not in json_dict:
                    return False

                for s in self._get_options():
                    json_value = json_dict[self.cfg_key].get(s.key)
                    if json_value is not None:
                        s.value = json_value

                # -- Read parented options
                parented_opts = self._get_parented_options()
                for parent_key, settings_dict in parented_opts.items():
                    for key, value in settings_dict.items():
                        json_value = json_dict[self.cfg_key].get(parent_key, dict()).get(key)
                        if json_value is not None:
                            option = self._get_option_by_key(key, parent_key)
                            option.value = json_value
        except Exception as e:
            logging.error('Error reading FSR settings from cfg file: %s', e)
            return False
        return True

    def write_cfg(self, plugin_path) -> bool:
        cfg = plugin_path / OPEN_VR_FSR_CFG

        try:
            with open(cfg, 'w') as f:
                json.dump(self.to_ini_js(), f, indent=2)
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
        return [s.to_js_object(export) for s in self._get_all_options()]

    def to_ini_js(self):
        options = {s.key: s.value for s in self._get_options()}
        options.update(self._get_parented_options())

        return {self.cfg_key: options}

    def from_js_dict(self, json_list):
        if not json_list:
            return

        for s in json_list:
            for setting in self._get_all_options():
                if setting.key == s.get('key') and setting.parent == s.get('parent'):
                    setting.value = s.get('value')
