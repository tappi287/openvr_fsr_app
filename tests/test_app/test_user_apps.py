import logging
import json

from app import app_fn
from conftest import test_user_app_id, user_app_path

LOGGER = logging.getLogger(__name__)


def test_add_custom_app_fn(app_settings):
    user_app = app_settings.user_apps.get(test_user_app_id)
    app_settings.user_apps = dict()
    app_settings.user_app_counter = 0

    result_dict = json.loads(app_fn.add_custom_app_fn(user_app))
    LOGGER.info(f'Result: {result_dict["msg"]}')

    user_app = app_settings.user_apps.get('#Usr001')

    assert result_dict['result'] is True
    assert 'User Test App' == user_app.get('name')
    assert user_app.get('path') == user_app_path.as_posix()


def test_remove_custom_app_fn(app_settings):
    user_app = app_settings.user_apps.get(test_user_app_id)
    result_dict = json.loads(app_fn.remove_custom_app_fn(user_app))

    assert result_dict['result'] is True
    assert len(app_settings.user_apps.keys()) == 0
