import json
import logging
from pathlib import Path

import app.util.scan_app_lib
from app import app_fn
from app.mod import FsrMod, FoveatedMod, VRPerfKitMod
from tests.conftest import test_app_path, user_app_path, test_user_app_id

LOGGER = logging.getLogger(__name__)

test_keys = {'name', 'path', 'openVrDllPaths', 'openVrDllPathsSelected', 'executablePaths', 'executablePathsSelected',
             'openVr', 'appid', 'settings', 'fsrInstalled', 'fsrVersion', 'fov_settings', 'fovInstalled', 'fovVersion',
             'vrp_settings', 'vrpInstalled', 'vrpVersion'}


def test_add_custom_library(app_settings, input_path, custom_lib_path, custom_dir_id, custom_app_id):
    # -- Test adding non-existing dir
    non_existing_test_path = Path('.') / 'non_existing_test_dir'
    result_dict = json.loads(app_fn.add_custom_dir_fn(non_existing_test_path.as_posix()))
    assert result_dict['result'] is False

    # -- Test add of custom test lib
    result_dict = json.loads(app_fn.add_custom_dir_fn(custom_lib_path.as_posix()))

    assert result_dict['result'] is True
    assert custom_dir_id in app_settings.user_app_directories

    apps = app_settings.load_steam_apps()
    assert custom_app_id in apps.keys()
    assert test_keys.difference(set(apps[custom_app_id].keys())) == set()

    app_settings.user_app_directories.pop(custom_dir_id)


def test_reduce_steam_apps_for_export(steam_apps_obj):
    reduced_apps = app_fn.reduce_steam_apps_for_export(steam_apps_obj.steam_apps)
    assert len(reduced_apps) == len(steam_apps_obj.steam_apps)


def test_load_steam_apps_with_mod_settings(steam_apps_obj):
    # -- Fake a scanned openVr
    steam_apps_obj.steam_apps['123']['openVr'] = True

    # -- Test
    new_steam_apps = app_fn._load_steam_apps_with_mod_settings(steam_apps_obj.steam_apps)

    assert len(new_steam_apps) == len(steam_apps_obj.steam_apps)

    mod_app = new_steam_apps.get('123')
    assert FsrMod.VAR_NAMES['settings'] in mod_app
    assert FoveatedMod.VAR_NAMES['settings'] in mod_app
    assert VRPerfKitMod.VAR_NAMES['settings'] in mod_app

    # -- Test with mod disk read
    new_steam_apps = app_fn._load_steam_apps_with_mod_settings(steam_apps_obj.steam_apps, scan_mod=True)
    assert len(new_steam_apps) == len(steam_apps_obj.steam_apps)

    mod_app = new_steam_apps.get('123')
    assert FsrMod.VAR_NAMES['settings'] in mod_app
    assert FsrMod.VAR_NAMES['installed'] in mod_app
    assert FoveatedMod.VAR_NAMES['settings'] in mod_app
    assert FoveatedMod.VAR_NAMES['installed'] in mod_app
    assert VRPerfKitMod.VAR_NAMES['settings'] in mod_app
    assert VRPerfKitMod.VAR_NAMES['installed'] in mod_app


def test_load_steam_lib_fn(app_settings):
    result_dict = json.loads(app_fn.load_steam_lib_fn())
    user_app = result_dict['data'][test_user_app_id]
    LOGGER.info(f'Result: {result_dict}')

    assert result_dict['result'] is True
    assert 'User Test App' == user_app.get('name')
    assert Path(user_app.get('path')) == user_app_path


def test_get_steam_lib_fn(steam_apps_obj):
    result_dict = json.loads(app_fn.scan_app_lib_fn())
    test_app = result_dict['data']['123']

    LOGGER.info(f'Result: {result_dict}')

    assert result_dict['result'] is True
    assert 'Test App' == test_app.get('name')
    assert test_app.get('path') == test_app_path.as_posix()


def test_scan_custom_lib(app_settings, custom_lib_path, custom_dir_id, custom_app_id, steam_apps_obj):
    app_settings.user_app_directories[custom_dir_id] = custom_lib_path.as_posix()

    result_dict = json.loads(app.util.scan_app_lib.scan_custom_libs_fn(custom_dir_id))
    apps = result_dict['data']

    assert result_dict['result'] is True
    assert custom_app_id in apps

    assert test_keys.difference(set(apps[custom_app_id].keys())) == set()

    app_settings.user_app_directories.pop(custom_dir_id)


def test_save_lib_fn(steam_apps_obj, custom_lib_path):
    # -- Test scan
    app_fn.add_custom_dir_fn(custom_lib_path.as_posix())
    result_dict = json.loads(app_fn.scan_app_lib_fn())
    test_apps = result_dict['data']

    # -- Test save
    app_fn.save_steam_lib(test_apps)

    # -- Load
    result_dict = json.loads(app_fn.load_steam_lib_fn())
    assert result_dict['result'] is True
