import json
import logging

from app import app_fn
from tests.conftest import test_app_path, user_app_path, test_user_app_id

LOGGER = logging.getLogger(__name__)


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
