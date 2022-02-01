import json
import logging
from pathlib import Path

from app import app_fn
from app.mod import FsrMod, FoveatedMod, VRPerfKitMod
from tests.conftest import test_app_path, user_app_path, test_user_app_id

LOGGER = logging.getLogger(__name__)

test_keys = {'name', 'path', 'openVrDllPaths', 'openVrDllPathsSelected', 'executablePaths', 'executablePathsSelected',
             'openVr', 'appid', 'settings', 'fsrInstalled', 'fsrVersion', 'fov_settings', 'fovInstalled', 'fovVersion',
             'vrp_settings', 'vrpInstalled', 'vrpVersion'}


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


def test_scan_app_lib_fn(app_settings, custom_dir_id, custom_lib_path, custom_app_id, steam_apps_obj):
    # -- Add non existing lib
    non_existing_id = custom_dir_id + '-'
    app_settings.user_app_directories[non_existing_id] = Path(custom_lib_path.parent / 'non-existing').as_posix()
    # -- Add custom test app lib
    app_settings.user_app_directories[custom_dir_id] = custom_lib_path.as_posix()

    # -- Test scan
    result_dict = json.loads(app_fn.scan_app_lib_fn())
    test_app = result_dict['data']['123']

    assert result_dict['result'] is True
    assert 'Test App' == test_app.get('name')
    assert custom_app_id in result_dict['data']
    assert test_app.get('path') == test_app_path.as_posix()


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
