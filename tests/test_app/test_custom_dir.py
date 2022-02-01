import json
from pathlib import Path

from app import app_fn
from test_app.test_app_fn import test_keys


def test_add_custom_library(app_settings, input_path, custom_lib_path, custom_dir_id, custom_app_id):
    app_settings.user_app_directories.pop(custom_dir_id, None)

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


def test_remove_custom_lib(app_settings, custom_lib_path, custom_dir_id, custom_app_id):
    app_settings.user_app_directories[custom_dir_id] = custom_lib_path

    # -- Test removing non-existing dir
    result_dict = json.loads(app_fn.remove_custom_dir_fn('#FakeDirId'))
    assert result_dict['result'] is False

    # -- Test remove of custom test lib
    result_dict = json.loads(app_fn.remove_custom_dir_fn(custom_dir_id))
    assert result_dict['result'] is True
    assert custom_dir_id not in app_settings.user_app_directories

    apps = app_settings.load_steam_apps()
    assert custom_app_id not in apps.keys()


def test_scan_custom_lib(app_settings, custom_lib_path, custom_dir_id, custom_app_id, steam_apps_obj):
    # -- Scan non existing lib
    non_existing_id = custom_dir_id + '-'
    app_settings.user_app_directories[non_existing_id] = Path(custom_lib_path.parent / 'non-existing').as_posix()
    result_dict = json.loads(app_fn.scan_custom_libs(non_existing_id))
    assert result_dict['result'] is False

    # -- Add custom test lib
    app_settings.user_app_directories[custom_dir_id] = custom_lib_path.as_posix()

    # -- Test scan
    result_dict = json.loads(app_fn.scan_custom_libs(custom_dir_id))
    apps = result_dict['data']

    assert result_dict['result'] is True
    assert custom_app_id in apps
    assert non_existing_id not in app_settings.user_app_directories

    assert test_keys.difference(set(apps[custom_app_id].keys())) == set()

    app_settings.user_app_directories.pop(custom_dir_id)
