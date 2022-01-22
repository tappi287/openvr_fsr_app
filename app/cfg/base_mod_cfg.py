import json
import logging
from pathlib import Path
from typing import List, Iterator

from app.globals import OPEN_VR_FSR_CFG
from app.util.utils import JsonRepr


class BaseModCfgSetting(JsonRepr):
    export_skip_keys = ['settings', 'category', 'desc', 'category']

    def __init__(self, key=None, name=None, value=None, desc=None,
                 settings=None, parent=None, category=None, hidden=False):
        self.key = key
        self.name = name
        self.desc = desc
        self.value = value
        self.settings = settings
        self.parent = parent
        self.category = category
        self.hidden = hidden


class BaseModSettings(JsonRepr):
    """ OpenVR Mod cfg base class to handle settings in openvr_mod.cfg configurations. """
    option_field_names = list()
    cfg_key = str()
    CFG_FILE = 'config_file.abc'

    def get_setting_fields(self) -> List[str]:
        options = list()
        for attr_name in dir(self):
            if isinstance(getattr(self, attr_name), BaseModCfgSetting):
                options.append(attr_name)
        return options

    def get_options(self) -> Iterator[BaseModCfgSetting]:
        for key in self.option_field_names:
            yield getattr(self, key)

    def get_option_by_key(self, key, parent_key=None) -> BaseModCfgSetting:
        for option in self.get_options():
            if option.parent == parent_key and key == option.key:
                return option

    def update_option(self, option_dict: dict):
        option = self.get_option_by_key(option_dict.get('key'), option_dict.get('parent'))
        if option:
            option.value = option_dict.get('value')

    def read_from_cfg(self, plugin_path: Path) -> bool:
        cfg = plugin_path / self.CFG_FILE
        if not cfg.exists():
            return False

        try:
            json_dict = self._cfg_to_json(cfg)

            # -- Check if the cfg key e.g. 'fsr' is defined inside the CFG
            if self.cfg_key not in json_dict:
                return False

            self.from_json(json_dict[self.cfg_key])
        except Exception as e:
            logging.error('Error reading FSR settings from cfg file: %s', e)
            return False
        return True

    def write_cfg(self, plugin_path) -> bool:
        cfg = plugin_path / self.CFG_FILE

        try:
            with open(cfg, 'w') as f:
                json.dump(self.to_cfg_json(), f, indent=2)
            logging.info('Written updated config at: %s', plugin_path)
        except Exception as e:
            logging.error('Error writing FSR settings to cfg file: %s', e)
            return False
        return True

    def delete_cfg(self, plugin_path) -> bool:
        cfg = plugin_path / self.CFG_FILE
        if not cfg.exists():
            return True

        try:
            cfg.unlink()
            logging.info('Deleted config at: %s', plugin_path)
        except Exception as e:
            logging.error('Error deleting FSR settings cfg file: %s', e)
            return False
        return True

    @staticmethod
    def _cfg_to_json(cfg_file: Path) -> dict:
        try:
            with open(cfg_file, 'r') as f:
                # -- Remove Inline Comments
                json_str = str()
                for line in f.readlines():
                    if '//' not in line and '#' not in line:
                        json_str += line

                return json.loads(json_str)
        except Exception as e:
            logging.error(f'Error reading CFG file {cfg_file}: {e}')

        return dict()

    def to_js(self, export: bool = False) -> list:
        return [s.to_js_object(export) for s in self._get_options()]

    def to_cfg_json(self) -> dict:
        options_dict = dict()

        for o in self._get_options():
            if o.parent:
                parent_option = self._get_option_by_key(o.parent)
                if parent_option.key not in options_dict:
                    options_dict[parent_option.key] = dict()
                options_dict[parent_option.key][o.key] = o.value
            else:
                options_dict[o.key] = o.value

        return {self.cfg_key: options_dict}

    def from_json(self, settings: dict):
        for key, value in settings.items():
            if isinstance(value, dict):
                self._update_option(value)
            else:
                self._update_option({'key': key, 'value': value})

    def from_js_dict(self, js_object_list: list):
        if not js_object_list:
            return

        for option_obj in js_object_list:
            self._update_option(option_obj)
