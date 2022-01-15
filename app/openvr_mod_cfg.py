import json
import logging
from pathlib import Path
from typing import List, Iterator, Dict, Any

from app.globals import OPEN_VR_FSR_CFG
from app.utils import JsonRepr


class OpenVRModCfgSetting(JsonRepr):
    export_skip_keys = ['settings', 'category']

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

        self.skip_option_keys = set(self.export_skip_keys).union(self.skip_keys)


class OpenVRModSettings(JsonRepr):
    """ OpenVR Mod cfg base class to handle settings in openvr_mod.cfg configurations. """
    option_field_names = list()
    cfg_key = str()

    def get_setting_fields(self) -> List[str]:
        options = list()
        for attr_name in dir(self):
            if isinstance(getattr(self, attr_name), OpenVRModCfgSetting):
                options.append(attr_name)
        return options

    def _get_options(self) -> Iterator[OpenVRModCfgSetting]:
        for key in self.option_field_names:
            option = getattr(self, key)
            if not option.parent:
                yield option

    def _get_all_options(self) -> Iterator[OpenVRModCfgSetting]:
        for key in self.option_field_names:
            yield getattr(self, key)

    def _get_option_by_key(self, key, parent_key=None) -> OpenVRModCfgSetting:
        for option in self._get_all_options():
            if option.parent == parent_key and key == option.key:
                return option

    def _get_parented_options(self) -> Dict[str, Dict[str, Any]]:
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
        return [s.to_js_object(export) for s in self._get_all_options()]

    def to_ini_js(self) -> dict:
        options = {s.key: s.value for s in self._get_options()}
        options.update(self._get_parented_options())

        return {self.cfg_key: options}

    def from_json(self, settings: dict):
        for key, value in settings.items():
            if isinstance(value, dict):
                for child_key, child_v in value.items():
                    option = self._get_option_by_key(key, child_key)
                    if option:
                        option.value = child_v
            else:
                option = self._get_option_by_key(key)
                if option:
                    option.value = value

    def from_js_dict(self, js_object_list: list):
        if not js_object_list:
            return

        for s in js_object_list:
            option = self._get_option_by_key(s.get('key'), s.get('parent'))
            if option:
                option.value = s.get('value')
