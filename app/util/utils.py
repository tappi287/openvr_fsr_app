import enum
import hashlib
import json
import logging
import os
import os.path
import re
import subprocess as sp
from datetime import datetime
from pathlib import Path, WindowsPath
from typing import Tuple, Union, Optional, IO

import eel
import gevent.event
from ruamel.yaml import YAML, CommentedMap, CommentedSeq

from app.globals import get_settings_dir, APP_NAME


def create_file_safe_name(filename: str, allow_spaces: bool = False) -> str:
    """ Replace any non alphanumeric characters from a string expect minus/underscore/period """
    if not allow_spaces:
        return re.sub('[^\\w\\-_.]', '_', filename)
    return re.sub('[^\\w\\- _.]', '_', filename)


class JsonRepr:
    skip_keys = list()
    export_skip_keys = list()
    after_load_callback: Optional[callable] = None
    before_save_callback: Optional[callable] = None

    @staticmethod
    def update_skip_keys(keys):
        return set(keys).union({'skip_keys', 'export_skip_keys'})

    def to_js_object(self, export: bool = False) -> dict:
        if self.before_save_callback:
            self.before_save_callback()

        self.skip_keys = self.update_skip_keys(self.skip_keys)

        js_dict = dict()
        for k, v in self.__dict__.items():
            if (export and k in self.export_skip_keys) or k in self.skip_keys:
                continue
            if k[:2] == '__' or callable(v) or isinstance(v, (classmethod, staticmethod)):
                continue

            js_dict[k] = v
        return js_dict

    def from_js_dict(self, json_dict):
        self.skip_keys = self.update_skip_keys(self.skip_keys)

        for k, v in json_dict.items():
            if k in self.skip_keys:
                continue
            setattr(self, k, v)

        if self.after_load_callback:
            self.after_load_callback()

    def set_missing_defaults(self):
        """ Set this as after load callback to make sure all defined
            default options are there.
        """
        if hasattr(self, 'defaults') and hasattr(self, 'options'):
            # -- Set defaults that were not loaded
            for k, opt in self.defaults.items():
                if k not in self.options:
                    self.options[k] = opt

            # -- Remove options no longer available
            for k, opt in self.options.items():
                if k not in self.defaults:
                    self.options.pop(k)


class AppExceptionHook:
    app = None
    event = gevent.event.Event()
    gui_msg = ''
    produce_exception = False

    @classmethod
    def exception_hook(cls, etype, value, tb):
        """ sys.excepthook will call this method """
        import traceback

        # Print exception
        traceback.print_exception(etype, value, tb)

        # Log exception
        stacktrace_msg = ''.join(traceback.format_tb(tb))
        if etype:
            exception_msg = '{0}: {1}'.format(etype, value)
        else:
            exception_msg = 'Exception: {}'.format(value)

        logging.critical(stacktrace_msg)
        logging.critical(exception_msg)

        # Write to exception log file
        exception_file_name = datetime.now().strftime(f'{APP_NAME}_Exception_%Y-%m-%d_%H%M%S.log')
        exception_file = Path(get_settings_dir()) / exception_file_name

        with open(exception_file, 'w') as f:
            traceback.print_exception(etype, value, tb, file=f)

        cls.gui_msg = f'{stacktrace_msg}\n{exception_msg}'
        cls.event.set()

    @classmethod
    def set_exception(cls, e: BaseException):
        cls.exception_hook(type(e), e, e.__traceback__)

    @staticmethod
    def test_exception():
        a = 1 / 0

    @staticmethod
    def exception_event_loop():
        if AppExceptionHook.event.is_set():
            logging.warning('Reporting App exception to front end')
            eel.app_exception(AppExceptionHook.gui_msg)
            AppExceptionHook.event.clear()


def capture_app_exceptions(func):
    """ Decorator to capture exceptions at app level """
    def func_wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            AppExceptionHook.set_exception(e)

    return func_wrapper


def execute_powershell_cmd(cmd: str) -> Tuple[int, Union[bytes, str], Union[bytes, str]]:
    p = sp.Popen(['powershell', cmd], **subprocess_args())
    out, err = p.communicate(timeout=5.0)

    if out:
        logging.debug('Powershell output: %s', out)
    if err:
        logging.error('Powershell error output: %s', err)

    return p.returncode, out, err


def create_shortcut(executable_path: Path, working_directory: Path, shortcut_location: Path,
                    arguments: str = ''):
    """ Create a Windows .lnk ShortCut file with powershell

    $Shell = New-Object -ComObject ("WScript.Shell")
    $ShortCut = $Shell.CreateShortcut($env:USERPROFILE + "\Desktop\Your Shortcut.lnk")
    $ShortCut.TargetPath="yourexecutable.exe"
    $ShortCut.Arguments="-arguementsifrequired"
    $ShortCut.WorkingDirectory = "c:\your\executable\folder\path";
    $ShortCut.WindowStyle = 1;
    $ShortCut.Hotkey = "CTRL+SHIFT+F";
    $ShortCut.IconLocation = "yourexecutable.exe, 0";
    $ShortCut.Description = "Your Custom Shortcut Description";
    $ShortCut.Save()

    :param executable_path: Path to the executable
    :param working_directory: Path to the working dir, appearing as "Start in" parameter in shortcut properties
    :param shortcut_location: Path to where to save the shortcut
    :param arguments: Additional arguments provided to the executable
    :return:
    """
    shell = '$Shell = New-Object -ComObject ("WScript.Shell")'
    loc = f'$ShortCut = $Shell.CreateShortcut("{str(WindowsPath(shortcut_location))}")'
    target = f'$ShortCut.TargetPath="{str(WindowsPath(executable_path))}"'
    arguments = f'$ShortCut.Arguments="{arguments}"'
    cwd = f'$ShortCut.WorkingDirectory = "{str(WindowsPath(working_directory))}"'

    cmd = f'{shell};{loc};{target};{arguments};{cwd};$ShortCut.Save()'

    return_code, _, _ = execute_powershell_cmd(cmd)
    return False if return_code != 0 else True


def start_lnk_from_powershell(shortcut: Path):
    cmd = f'Invoke-Item -Path "{str(WindowsPath(shortcut))}"'
    return_code, _, _ = execute_powershell_cmd(cmd)
    return False if return_code != 0 else True


# https://github.com/pyinstaller/pyinstaller/wiki/Recipe-subprocess
# Create a set of arguments which make a ``subprocess.Popen`` (and
# variants) call work with or without Pyinstaller, ``--noconsole`` or
# not, on Windows and Linux. Typical use::
#
#   subprocess.call(['program_to_run', 'arg_1'], **subprocess_args())
#
# When calling ``check_output``::
#
#   subprocess.check_output(['program_to_run', 'arg_1'],
#                           **subprocess_args(False))
def subprocess_args(include_stdout=True, cwd=None):
    # The following is true only on Windows.
    if hasattr(sp, 'STARTUPINFO'):
        # On Windows, subprocess calls will pop up a command window by default
        # when run from Pyinstaller with the ``--noconsole`` option. Avoid this
        # distraction.
        si = sp.STARTUPINFO()
        si.dwFlags |= sp.STARTF_USESHOWWINDOW
        # Windows doesn't search the path by default. Pass it an environment so
        # it will.
        env = os.environ
    else:
        si = None
        env = None

    # ``subprocess.check_output`` doesn't allow specifying ``stdout``::
    #
    #   Traceback (most recent call last):
    #     File "test_subprocess.py", line 58, in <module>
    #       **subprocess_args(stdout=None))
    #     File "C:\Python27\lib\subprocess.py", line 567, in check_output
    #       raise ValueError('stdout argument not allowed, it will be overridden.')
    #   ValueError: stdout argument not allowed, it will be overridden.
    #
    # So, add it only if it's needed.
    if include_stdout:
        ret = {'stdout': sp.PIPE}
    else:
        ret = {}

    # On Windows, running this from the binary produced by Pyinstaller
    # with the ``--noconsole`` option requires redirecting everything
    # (stdin, stdout, stderr) to avoid an OSError exception
    # "[Error 6] the handle is invalid."
    ret.update({'stdin': sp.PIPE,
                'stderr': sp.PIPE,
                'startupinfo': si,
                'env': env,
                'cwd': cwd})
    return ret


def find_subclasses(module, clazz):
    for name in dir(module):
        o = getattr(module, name)
        try:
            if (o != clazz) and issubclass(o, clazz):
                yield name, o
        except TypeError:
            pass


class SizeUnit(enum.Enum):
    BYTES = 1
    KB = 2
    MB = 3
    GB = 4


def convert_unit(size_in_bytes, unit):
    """ Convert the size from bytes to other units like KB, MB or GB"""
    size_in_bytes = int(size_in_bytes)
    if unit == SizeUnit.KB:
        return size_in_bytes / 1024
    elif unit == SizeUnit.MB:
        return size_in_bytes / (1024 * 1024)
    elif unit == SizeUnit.GB:
        return size_in_bytes / (1024 * 1024 * 1024)
    else:
        return size_in_bytes


def get_file_hash(file):
    md5 = hashlib.md5()
    with open(file, 'rb') as f:
        buf = f.read()
        md5.update(buf)
    return md5.hexdigest()


def read_json_cfg(f: IO):
    # -- Remove Inline Comments
    json_str = str()
    for line in f.readlines():
        if '//' not in line and '#' not in line:
            json_str += line

    return json.loads(json_str)


class ModCfgYamlHandler:
    yaml = YAML()

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
    def write_cfg(cls, settings, target_file) -> bool:
        """ Write settings to a file

        :param app.cfg.base_mod_cfg.BaseModSettings settings:
        :param Path target_file:
        """
        data = cls._prepare_yaml_data(settings, target_file, True)
        try:
            cls.yaml.dump(data, target_file)
        except Exception as e:
            logging.error('Error writing Yaml file: %s', e)
            return False
        return True

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
                cls.set_data(data, settings, current_data[k], k, key)
        elif isinstance(current_data, list):
            for item in current_data:
                cls.set_data(data, settings, item, parent_key)

        option = settings.get_option_by_key(key, parent_key)

        match option is not None:
            # -- Update data from settings
            case True if write and parent_key:
                cls.set_value(data[parent_key], key, option.value)
            case True if write and not parent_key and not option.hidden:
                cls.set_value(data, key, option.value)
            # -- Update settings from data
            case True if not write:
                option.value = current_data

    @classmethod
    def set_value(cls, data, key, value):
        """ Update Yaml CommentedMap with a compatible representation value

        :param CommentedMap data:
        :param str key:
        :param Any value:
        :return:
        """
        match type(value).__name__:
            case 'float':
                node = cls.yaml.representer.represent_data(value)
                data[key] = cls.yaml.constructor.construct_object(node)
            case 'list':
                for idx, item in enumerate(value):
                    data[key][idx] = item
            case _:
                data[key] = value

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
