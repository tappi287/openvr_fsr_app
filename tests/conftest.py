import shutil

import pytest
from pathlib import Path, WindowsPath
from distutils.dir_util import copy_tree

import app
import app.mod
from app.app_settings import AppSettings
from app.util.manifest_worker import ManifestWorker
from app.mod import get_available_mods

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
test_data_output_path = Path(__file__).parent / 'data' / 'output'

user_app_path = test_data_input_path / 'user_app'
test_app_path = test_data_input_path / 'steamapps' / 'common' / 'test_app'
test_user_app_id = 'Usr#001'
app_dir = Path(__file__).parent.parent

# -- CleanUp Test settings files/app cache
test_settings_file = app.globals.get_settings_dir() / app.globals.SETTINGS_FILE_NAME
test_settings_file.unlink(missing_ok=True)
test_apps_file = app.globals.get_settings_dir() / app.globals.APPS_STORE_FILE_NAME
test_apps_file.unlink(missing_ok=True)

# -- CleanUp Output Dir
shutil.rmtree(test_data_output_path, ignore_errors=True)
test_data_output_path.mkdir(exist_ok=True)


@pytest.fixture(scope='session')
def input_path():
    return test_data_input_path


@pytest.fixture(scope='session')
def output_path():
    return test_data_output_path


@pytest.fixture(scope='session')
def open_vr_fsr_test_mod_dir():
    return test_data_input_path / 'mod_dir'


@pytest.fixture(scope='session')
def open_vr_fsr_dir():
    return app_dir / 'data' / 'openvr_fsr'


@pytest.fixture(scope='session')
def vrperfkit_dir():
    return app_dir / 'data' / 'vrperfkit'


@pytest.fixture(scope='session')
def steam_test_path():
    base_path = Path(__file__).parent
    return Path(base_path / 'data' / 'input').absolute()


@pytest.fixture
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


def _setup_manifest_paths(manifest):
    openvr_paths = [p for p in ManifestWorker.find_open_vr_dll(Path(manifest.get('path')))]
    executable_path_ls = [p for p in ManifestWorker.find_executables(Path(manifest.get('path')))]
    manifest['openVrDllPaths'] = [p.as_posix() for p in openvr_paths]
    manifest['openVrDllPathsSelected'] = [p.as_posix() for p in openvr_paths]
    manifest['executablePaths'] = [p.as_posix() for p in executable_path_ls]
    manifest['executablePathsSelected'] = [p.as_posix() for p in executable_path_ls]
    manifest['openVr'] = True


def _setup_manifest_mods(manifest):
    # -- Add Mod specific data
    for mod_obj in get_available_mods(manifest):
        manifest[mod_obj.VAR_NAMES['settings']] = mod_obj.settings.to_js(export=True)
        mod_obj.update_from_disk()
        manifest = mod_obj.manifest


@pytest.fixture
def test_app(steam_apps_obj):
    manifest = steam_apps_obj.steam_apps.get('123')

    _setup_manifest_paths(manifest)
    _setup_manifest_mods(manifest)

    return manifest


@pytest.fixture
def test_app_writeable(steam_apps_obj):
    manifest = steam_apps_obj.steam_apps.get('124')

    # -- Create writeable App Copy in output
    new_path = test_data_output_path / Path(manifest.get('path')).name
    copy_tree(Path(manifest.get('path')).as_posix(), new_path.as_posix())

    manifest['path'] = new_path.as_posix()

    _setup_manifest_paths(manifest)
    _setup_manifest_mods(manifest)

    steam_apps_obj.steam_apps['124'] = manifest
    return manifest


@pytest.fixture
def app_settings(steam_apps_obj):
    manifest = {
        'appid': test_user_app_id,
        "name": 'User Test App',
        'path': user_app_path.as_posix(),
        'sizeGb': 0, 'SizeOnDisk': 0,
        'userApp': True,
    }

    _setup_manifest_paths(manifest)
    _setup_manifest_mods(manifest)

    AppSettings.user_apps[test_user_app_id] = manifest
    return AppSettings


@pytest.fixture
def outdated_apps_app_settings(steam_apps_obj):
    manifest = {
        'appid': test_user_app_id,
        "name": 'User Test App',
        'path': user_app_path.as_posix(),
        'sizeGb': 0, 'SizeOnDisk': 0,
        'userApp': True,
    }

    _setup_manifest_paths(manifest)
    _setup_manifest_mods(manifest)

    # -- Remove new
    manifest.pop(app.mod.VRPerfKitMod.VAR_NAMES['settings'])
    manifest.pop(app.mod.VRPerfKitMod.DLL_LOC_KEY_SELECTED)
    manifest.pop(app.mod.VRPerfKitMod.DLL_LOC_KEY)

    AppSettings.user_apps[test_user_app_id] = manifest
    return AppSettings
