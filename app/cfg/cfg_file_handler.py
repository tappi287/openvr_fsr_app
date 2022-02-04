import json
import logging
import shutil
from pathlib import Path

from ruamel.yaml import YAML, CommentedMap


class ModCfgJsonHandler:
    @classmethod
    def read_cfg(cls, settings, cfg_file) -> dict:
        """ Update a ModSettings object from an CFG file

        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :param Path cfg_file:
        :return:
        """
        # -- Read json
        json_data = cls.read_json_cfg(cfg_file)

        # -- Check if the cfg key e.g. 'fsr' is defined inside the CFG
        if settings.cfg_key not in json_data:
            return dict()

        # -- Update settings from json data
        cls.from_json_data(json_data[settings.cfg_key], settings)
        return json_data[settings.cfg_key]

    @classmethod
    def write_cfg(cls, settings, cfg_file):
        """ Write ModSettings object into a json file .cfg

        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :param Path cfg_file:
        :return:
        """
        with open(cfg_file, 'w') as f:
            json.dump(cls.to_cfg_json(settings), f, indent=2)

    @staticmethod
    def read_json_cfg(file: Path):
        with open(file, 'r') as f:
            # -- Remove Inline Comments
            json_str = str()
            for line in f.readlines():
                if '//' not in line and '#' not in line:
                    json_str += line

        return json.loads(json_str)

    @staticmethod
    def from_json_data(json_data: dict, settings):
        """ Update a ModSettings object from json dict

        :param json_data:
        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :return:
        """
        for key, value in json_data.items():
            if isinstance(value, dict):
                option = settings.get_option_by_key(value.get('key'), value.get('parent'))
                if option:
                    option.value = value.get('value')
            else:
                option = settings.get_option_by_key(key)
                if option:
                    option.value = value

    @staticmethod
    def to_cfg_json(settings) -> dict:
        """ Serialize ModSettings object into a json dict

        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :return:
        """
        options_dict = dict()

        for o in settings.get_options():
            if o.parent:
                parent_option = settings.get_option_by_key(o.parent)
                if parent_option.key not in options_dict:
                    options_dict[parent_option.key] = dict()
                options_dict[parent_option.key][o.key] = o.value
            else:
                options_dict[o.key] = o.value

        return {settings.cfg_key: options_dict}


class ModCfgYamlHandler:
    yaml = YAML()
    BACK_UP_SUFFIX = '.orig'

    @staticmethod
    def create_backup(file: Path):
        try:
            back_up_file = file.with_name(f'{file.name}{ModCfgYamlHandler.BACK_UP_SUFFIX}')
            back_up_file.unlink(missing_ok=True)

            shutil.copy(file, back_up_file)
        except Exception as e:
            logging.error('Error creating yml config back-up: %s', e)

    @classmethod
    def load_file(cls, file: Path) -> CommentedMap:
        with open(file, 'r') as f:
            data = cls.yaml.load(f)
        return data

    @classmethod
    def _prepare_yaml_data(cls, settings, file, write) -> CommentedMap:
        """ Prepare data to be written or update a settings object from read data.

        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :param Path file:
        :param bool write:
        :return:
        """
        data = CommentedMap()

        # -- Update from existing file
        if file.exists():
            data = cls.load_file(file)

        cls.update_data(data, settings, write)
        return data

    @classmethod
    def write_cfg(cls, settings, target_file):
        """ Write settings to a file

        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :param Path target_file:
        """
        cls.create_backup(target_file)
        data = cls._prepare_yaml_data(settings, target_file, True)
        cls.yaml.dump(data, target_file)

    @classmethod
    def read_cfg(cls, settings, cfg_file) -> CommentedMap:
        """ Read a cfg file and update settings object.

        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :param Path cfg_file: Cfg yaml file to be read
        """
        return cls._prepare_yaml_data(settings, cfg_file, False)

    @classmethod
    def update_data(cls, data, settings, write) -> CommentedMap:
        """ Update data from settings object or update settings object from data.

        :param CommentedMap data: data to be updated or read from
        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :param bool write: read or write
        """
        cls.set_data(data, settings, data, write=write)
        cls.set_style(data)
        return data

    @classmethod
    def set_data(cls, data, settings, current_data, key=None, parent_key=None, write=True):
        """ Traverse data fields and update either settings or data.

        :param CommentedMap data: Un-traversed complete data
        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :param CommentedMap | Any current_data: currently traversed child data set
        :param str | None key: current data key
        :param str | None parent_key: current data parent key
        :param bool write: update data or settings object
        :return:
        """
        if isinstance(current_data, dict):
            for k in current_data:
                cls.set_data(data, settings, current_data[k], k, key, write=write)
        elif isinstance(current_data, list):
            for item in current_data:
                cls.set_data(data, settings, item, parent_key, write=write)

        option = settings.get_option_by_key(key, parent_key)

        match option is not None:
            # -- Update data from settings
            case True if write and parent_key:
                cls.set_value(data[parent_key], key, option.value)
            case True if write and not parent_key and not option.hidden:
                cls.set_value(data, key, option.value)
            # -- Update settings from data
            case True if not write:
                option.value = cls.get_value(current_data)

    @classmethod
    def set_value(cls, data, key, value):
        """ Update Yaml CommentedMap with a compatible representation value

        :param CommentedMap data:
        :param str key:
        :param Any value:
        :return:
        """
        match type(value).__name__:
            # -- construct Float
            case 'float':
                node = cls.yaml.representer.represent_data(value)
                data[key] = cls.yaml.constructor.construct_object(node)
            # -- update CommentedSeq
            case 'list' if isinstance(data[key], list):
                for idx, item in enumerate(value):
                    data[key][idx] = item
            # -- bool, str, int
            case _:
                data[key] = value

    @classmethod
    def get_value(cls, yml_value):
        """ Read back Yaml values to std Python types """
        match type(yml_value).__name__:
            case 'ScalarFloat':
                return float(yml_value)
            case 'CommentedSeq':
                return list(yml_value)
            case 'CommentedMap':
                return dict(yml_value)
            case _:
                return yml_value

    @classmethod
    def set_style(cls, d, map_flow=False, list_flow=True):
        """ Setup Yaml flow/block style

        :param CommentedMap | CommentedSeq | Any d:
        :param bool map_flow:
        :param bool list_flow:
        """
        match type(d).__name__:
            case 'CommentedMap':
                if map_flow:
                    d.fa.set_flow_style()
                else:
                    d.fa.set_block_style()
                for k in d:
                    cls.set_style(d[k], map_flow, list_flow)
            case 'CommentedSeq':
                if list_flow:
                    d.fa.set_flow_style()
                else:
                    d.fa.set_block_style()
                for item in d:
                    cls.set_style(item, map_flow, list_flow)
