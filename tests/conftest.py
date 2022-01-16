import pytest
from pathlib import Path, WindowsPath

import app
from app.app_settings import AppSettings
from app.manifest_worker import ManifestWorker
from app.openvr_mod import get_available_mods

libraryfolders_content = '''"libraryfolders"
{{
	"contentstatsid"		"1234"
	"0"
	{{
		"path"		"{path}"
	}}
}}
'''
test_data_input_path = Path(__file__).parent / 'data' / 'input'
user_app_path = test_data_input_path / 'user_app'
test_app_path = test_data_input_path / 'steamapps' / 'common' / 'test_app'
test_user_app_id = 'Usr#001'
app_dir = Path(__file__).parent.parent


@pytest.fixture(scope='session')
def open_vr_fsr_dir():
    return app_dir / 'data' / 'openvr_fsr'


@pytest.fixture(scope='session')
def open_vr_fsr_test_dir():
    return test_data_input_path / 'mod_dir'


@pytest.fixture(scope='session')
def steam_test_path():
    base_path = Path(__file__).parent
    return Path(base_path / 'data' / 'input').absolute()


@pytest.fixture(scope='session')
def steam_apps_obj(steam_test_path):
    # -- Define Steam Library path in test input dir
    with open(steam_test_path / app.steam.STEAM_APPS_FOLDER / app.steam.STEAM_LIBRARY_FILE, 'w') as f:
        f.write(
            libraryfolders_content.format(path=str(WindowsPath(steam_test_path)))
        )

    # -- Re-route Steam Location to test directory
    steam_apps = app.steam.apps
    app.steam.SteamApps.STEAM_LOCATION = steam_test_path

    # -- Read Steam Apps
    steam_apps.read_steam_library()
    steam_apps.steam_apps.pop(app.steam.STEAM_LIBRARY_FOLDERS)

    return steam_apps


@pytest.fixture(scope='session')
def test_app(steam_apps_obj):
    manifest = steam_apps_obj.steam_apps.get('123')

    openvr_paths = [p for p in ManifestWorker.find_open_vr_dll(Path(manifest.get('path')))]
    manifest['openVrDllPaths'] = [p.as_posix() for p in openvr_paths]
    manifest['openVrDllPathsSelected'] = [p.as_posix() for p in openvr_paths]
    manifest['openVr'] = True

    # -- Add Mod specific data
    for mod_obj in get_available_mods(manifest):
        manifest[mod_obj.VAR_NAMES['settings']] = mod_obj.settings.to_js(export=True)
        manifest[mod_obj.VAR_NAMES['installed']] = mod_obj.update_from_disk()
        manifest[mod_obj.VAR_NAMES['version']] = mod_obj.get_version()

    return manifest


@pytest.fixture(scope='function')
def app_settings(steam_apps_obj):
    openvr_paths = [p for p in ManifestWorker.find_open_vr_dll(user_app_path)]
    manifest = {
        'appid': test_user_app_id,
        "name": 'User Test App',
        'path': user_app_path.as_posix(),
        'openVrDllPaths': [p.as_posix() for p in openvr_paths],
        'openVrDllPathsSelected': [p.as_posix() for p in openvr_paths],
        'openVr': True,
        'sizeGb': 0, 'SizeOnDisk': 0,
        'userApp': True,
    }

    # -- Add Mod specific data
    for mod_obj in get_available_mods(manifest):
        manifest[mod_obj.VAR_NAMES['settings']] = mod_obj.settings.to_js(export=True)
        manifest[mod_obj.VAR_NAMES['installed']] = False
        manifest[mod_obj.VAR_NAMES['version']] = mod_obj.get_version()

    AppSettings.user_apps[test_user_app_id] = manifest
    return AppSettings
