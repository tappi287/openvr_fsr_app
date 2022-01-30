import logging
import json
from pathlib import Path

from app import app_fn
from tests.conftest import user_app_path

LOGGER = logging.getLogger(__name__)


def test_add_custom_app_fn(app_settings, user_app):
    # -- Remove Text env user app first
    app_fn.remove_custom_app_fn(user_app)

    result_dict = json.loads(app_fn.add_custom_app_fn(user_app))
    LOGGER.info(f'Result: {result_dict["msg"]}')

    assert result_dict['result'] is True
    assert 'User Test App' == user_app.get('name')
    assert Path(user_app.get('path')) == user_app_path


def test_remove_custom_app_fn(app_settings, user_app):
    result_dict = json.loads(app_fn.remove_custom_app_fn(user_app))

    assert result_dict['result'] is True
