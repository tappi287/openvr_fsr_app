import logging
from pathlib import Path

from tests.conftest import test_app_path

LOGGER = logging.getLogger(__name__)


def test_load_steam_lib(steam_apps_obj, steam_test_path):
    for app_id, app_dict in steam_apps_obj.steam_apps.items():
        LOGGER.info(f'{app_id}: {app_dict.get("name")} path: {app_dict.get("path")}')

    assert '123' in steam_apps_obj.steam_apps
    assert 'Test App' == steam_apps_obj.steam_apps['123']['name']
    assert test_app_path == Path(steam_apps_obj.steam_apps['123']['path'])
