import shutil
from typing import Tuple

import pytest
from pathlib import Path, WindowsPath
from distutils.dir_util import copy_tree, remove_tree

import app
import app.mod
import app.app_fn
from app.app_settings import AppSettings
from app.util.manifest_worker import ManifestWorker
from app.util.utils import get_name_id
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
test_user_app_id = f'{app.globals.USER_APP_PREFIX}_{get_name_id(user_app_path.stem)}'
app_dir = Path(__file__).parent.parent

# -- CleanUp Test settings files/app cache
test_settings_file = app.globals.get_settings_dir() / app.globals.SETTINGS_FILE_NAME
test_settings_file.unlink(missing_ok=True)
test_apps_file = app.globals.get_settings_dir() / app.globals.APPS_STORE_FILE_NAME
test_apps_file.unlink(missing_ok=True)

# -- CleanUp Output Dir
shutil.rmtree(test_data_output_path, ignore_errors=True)
test_data_output_path.mkdir(exist_ok=True)


def create_manipulated_settings(test_app_manifest, test_keys_values: Tuple[list, list], mod) -> Tuple[dict, list]:
    """ Create Test Settings """
    test_settings = list()

    for _key_pair, _test_value in zip(test_keys_values[0], test_keys_values[1]):
        _key, _parent = _key_pair
        test_setting = {'key': _key, 'parent': _parent, 'value': _test_value}
        test_settings.append(test_setting)

    # -- Manipulate example settings
    mod_settings = test_app_manifest[mod.VAR_NAMES['settings']]
    for _s in mod_settings:
        for _test_s in test_settings:
            if _s.get('key') == _test_s.get('key') and _s.get('parent') == _test_s.get('parent'):
                _s['value'] = _test_s.get('value')

    return test_app_manifest, test_settings


@pytest.fixture(scope='session')
def input_path():
    return test_data_input_path


@pytest.fixture(scope='session')
def output_path():
    return test_data_output_path


@pytest.fixture(scope='session')
def custom_lib_path(input_path):
    return input_path / 'custom_dir'


@pytest.fixture(scope='session')
def custom_dir_id(custom_lib_path):
    return f'{app.globals.CUSTOM_APP_PREFIX}{get_name_id(custom_lib_path.as_posix())}'


@pytest.fixture(scope='session')
def custom_app_id(custom_dir_id, custom_lib_path):
    custom_app_path = custom_lib_path / "custom_app_writeable"
    return f'{custom_dir_id}_{get_name_id(custom_app_path.as_posix())}'


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


def _create_writeable_test_app(steam_apps_obj, app_id):
    manifest = steam_apps_obj.steam_apps.get(app_id)

    # -- Create writeable App Copy in output
    new_path = test_data_output_path / Path(manifest.get('path')).name
    if new_path.exists():
        remove_tree(new_path.as_posix(), verbose=0)
    copy_tree(Path(manifest.get('path')).as_posix(), new_path.as_posix())

    manifest['path'] = new_path.as_posix()

    _setup_manifest_paths(manifest)
    _setup_manifest_mods(manifest)

    steam_apps_obj.steam_apps[app_id] = manifest
    return manifest


@pytest.fixture(scope='function')
def test_app_writeable(steam_apps_obj):
    return _create_writeable_test_app(steam_apps_obj, '124')


def pytest_generate_tests(metafunc):
    if "app_settings" in metafunc.fixturenames:
        metafunc.parametrize("app_settings", ["app_settings_old", "app_settings"], indirect=True)


@pytest.fixture
def user_app():
    manifest = {
        'appid': test_user_app_id,
        "name": 'User Test App',
        'path': user_app_path.as_posix(),
        'sizeGb': 0, 'SizeOnDisk': 0,
        'userApp': True,
    }
    _setup_manifest_paths(manifest)
    _setup_manifest_mods(manifest)

    return manifest


@pytest.fixture
def app_settings(request, steam_apps_obj, user_app):
    if request.param == "app_settings":
        AppSettings.mod_data_dirs = dict()
    elif request.param == "app_settings_old":
        AppSettings.SETTINGS_FILE_OVR = test_data_input_path / "settings_0.6.4.json"
        AppSettings.load()

    app.app_fn.add_custom_app_fn(user_app)
    return AppSettings
