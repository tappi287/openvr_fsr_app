import logging
from pathlib import Path
from shutil import copyfile
from typing import List, Iterator

from app.cfg import ModCfgJsonHandler, ModCfgYamlHandler
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


class BaseModCfgType:
    invalid = -1
    open_vr_mod = 0
    vrp_mod = 1


class BaseModSettings(JsonRepr):
    """ OpenVR Mod cfg base class to handle settings in openvr_mod.cfg configurations. """
    cfg_key = str()
    CFG_FILE = 'config_file.abc'
    CFG_TYPE = BaseModCfgType.invalid

    def __init__(self):
        self.option_field_names = self.get_setting_fields()

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
            match self.CFG_TYPE:
                case BaseModCfgType.open_vr_mod:
                    # -- Read settings to this instance from json
                    return self.update_from_json_cfg(cfg)
                case BaseModCfgType.vrp_mod:
                    # -- Read settings to this instance from yaml
                    return self.update_from_yaml_cfg(cfg)
        except Exception as e:
            logging.error('Error reading Settings from CFG file: %s', e)

        return False

    def write_cfg(self, plugin_path: Path, plugin_src_dir: Path) -> bool:
        cfg = plugin_path / self.CFG_FILE

        match self.CFG_TYPE:
            case BaseModCfgType.open_vr_mod:
                ModCfgJsonHandler.write_cfg(self, cfg)
            case BaseModCfgType.vrp_mod:
                if not cfg.exists():
                    copyfile(plugin_src_dir / cfg.name, cfg)
                ModCfgYamlHandler.write_cfg(self, cfg)
            case _:
                return False

        logging.info('Written updated config at: %s', plugin_path)
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

    def to_js(self, export: bool = False) -> list:
        return [s.to_js_object(export) for s in self.get_options()]

    def update_from_json_cfg(self, file: Path) -> bool:
        data = ModCfgJsonHandler.read_cfg(self, file)
        return True if data else False

    def update_from_yaml_cfg(self, file: Path) -> bool:
        # -- This updates this class directly
        data = ModCfgYamlHandler.read_cfg(self, file)

        # -- Restore empty data for hidden settings just defining parents
        for option in self.get_options():
            if option.hidden:
                option.value = dict()

        return True if data else False

    def from_js_dict(self, js_object_list: list):
        if not js_object_list:
            return

        for option_obj in js_object_list:
            self.update_option(option_obj)
