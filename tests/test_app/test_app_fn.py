import json
import logging

from app import app_fn
from tests.conftest import test_app_path, user_app_path, test_user_app_id

LOGGER = logging.getLogger(__name__)


def test_reduce_steam_apps_for_export(steam_apps_obj):
    reduced_apps = app_fn.reduce_steam_apps_for_export(steam_apps_obj.steam_apps)
    assert len(reduced_apps) == len(steam_apps_obj.steam_apps)


def test_load_steam_apps_with_mod_settings(steam_apps_obj):
    new_steam_apps = app_fn._load_steam_apps_with_mod_settings(steam_apps_obj.steam_apps)

    assert len(new_steam_apps) == len(steam_apps_obj.steam_apps)
    for app_id, manifest in new_steam_apps.items():
        assert 'userApp' in manifest
        if manifest.get('openVr') or manifest.get('vrpInstalled'):
            assert 'settings' in manifest


def test_load_steam_lib_fn(app_settings):
    result_dict = json.loads(app_fn.load_steam_lib_fn())
    user_app = result_dict['data'][test_user_app_id]
    LOGGER.info(f'Result: {result_dict}')

    assert result_dict['result'] is True
    assert 'User Test App' == user_app.get('name')
    assert user_app.get('path') == user_app_path.as_posix()


def test_load_steam_lib_outdated_settings_fn(outdated_apps_app_settings):
    result_dict = json.loads(app_fn.load_steam_lib_fn())
    user_app = result_dict['data'][test_user_app_id]
    LOGGER.info(f'Result: {result_dict}')

    assert result_dict['result'] is True
    assert 'User Test App' == user_app.get('name')
    assert user_app.get('path') == user_app_path.as_posix()


def test_get_steam_lib_fn():
    result_dict = json.loads(app_fn.get_steam_lib_fn())
    test_app = result_dict['data']['123']

    LOGGER.info(f'Result: {result_dict}')

    assert result_dict['result'] is True
    assert 'Test App' == test_app.get('name')
    assert test_app.get('path') == test_app_path.as_posix()
