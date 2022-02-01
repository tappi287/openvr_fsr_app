import json
import logging
import subprocess
from pathlib import WindowsPath, Path

import app
import app.mod
import app.util.utils
from app.app_settings import AppSettings
from app.mod import get_available_mods
from app.util.manifest_worker import run_update_steam_apps
from app.util.custom_app import create_custom_app, scan_custom_library
from app.util.utils import get_name_id


def reduce_steam_apps_for_export(steam_apps) -> dict:
    reduced_dict = dict()

    for app_id, entry in steam_apps.items():
        reduced_dict[app_id] = dict()
        # Add only necessary data
        reduced_dict[app_id]['name'] = entry.get('name')
        reduced_dict[app_id]['sizeGb'] = entry.get('sizeGb')
        reduced_dict[app_id]['path'] = entry.get('path')
        reduced_dict[app_id]['openVrDllPaths'] = entry.get('openVrDllPaths')
        reduced_dict[app_id]['openVrDllPathsSelected'] = entry.get('openVrDllPathsSelected')
        reduced_dict[app_id]['executablePaths'] = entry.get('executablePaths')
        reduced_dict[app_id]['executablePathsSelected'] = entry.get('executablePathsSelected')
        reduced_dict[app_id]['openVr'] = entry.get('openVr')
        reduced_dict[app_id]['SizeOnDisk'] = entry.get('SizeOnDisk')
        reduced_dict[app_id]['appid'] = entry.get('appid')

        # Mod specific data
        if entry.get('openVr') or entry.get('vrpInstalled'):
            for mod in app.mod.get_available_mods(entry):
                reduced_dict[app_id][mod.VAR_NAMES['settings']] = mod.settings.to_js(export=True)
                reduced_dict[app_id][mod.VAR_NAMES['installed']] = entry.get(mod.VAR_NAMES['installed'], False)
                reduced_dict[app_id][mod.VAR_NAMES['version']] = entry.get(mod.VAR_NAMES['version'], '')
            reduced_dict[app_id]['fsr_compatible'] = entry.get('fsr_compatible', True)

    return reduced_dict


def _load_steam_apps_with_mod_settings(steam_apps, scan_mod=False):
    """ Add or restore complete settings entries """
    for app_id, entry in steam_apps.items():
        if entry.get('openVr') or entry.get('vrpInstalled'):
            for mod in app.mod.get_available_mods(entry):
                if scan_mod:
                    mod.update_from_disk()
                entry[mod.VAR_NAMES['settings']] = mod.settings.to_js(export=False)

    return steam_apps


@app.utils.capture_app_exceptions
def save_steam_lib(steam_apps):
    logging.info('Updating SteamApp disk cache.')

    # -- Save disk cache
    for app_id, entry in steam_apps.items():
        if not app_id:
            continue
        if entry.get('_showDetails'):
            entry.pop('_showDetails')

    AppSettings.save_steam_apps(reduce_steam_apps_for_export(steam_apps))
    AppSettings.save()


@app.utils.capture_app_exceptions
def load_steam_lib_fn():
    """ Load saved SteamApps from disk """
    steam_apps = _load_steam_apps_with_mod_settings(AppSettings.load_steam_apps())

    re_scan_required = False

    # -- Re-create disk cache between versions
    if app.globals.get_version() != AppSettings.previous_version:
        re_scan_required = True

    # -- Re-scan lib if no cached apps other than user apps
    if not len(steam_apps.keys()):
        re_scan_required = True

    logging.debug(f'Loaded {len(steam_apps.keys())} Steam Apps from disk.')
    return json.dumps({'result': True, 'data': steam_apps, 'reScanRequired': re_scan_required})


def scan_custom_libs(dir_id: str):
    """ Scan and save a custom library """
    logging.debug(f'Reading Custom Library: {dir_id}')
    if dir_id not in AppSettings.user_app_directories:
        return json.dumps({'result': False, 'msg': f'Unknown Custom library with id: {dir_id}'})

    path = Path(AppSettings.user_app_directories.get(dir_id))
    if not path.exists():
        AppSettings.user_app_directories.pop(dir_id)
        AppSettings.save()
        return json.dumps({'result': False, 'msg': f'Non Existing library {path.as_posix()} removed.'})

    result_apps = scan_custom_library(dir_id, path)
    if not result_apps:
        return json.dumps({'result': False, 'msg': f'No Apps found in {dir_id}: {path.as_posix()}'})

    AppSettings.save_custom_dir_apps(dir_id, reduce_steam_apps_for_export(result_apps))

    return json.dumps({'result': True, 'data': result_apps})


@app.utils.capture_app_exceptions
def scan_app_lib_fn():
    """ Refresh SteamLib and re-scan every app directory """
    logging.debug('Reading Steam Library')

    # -- Load currently cached custom apps before
    #    they get overwritten by the scan
    cached_custom_apps = AppSettings.load_custom_dir_apps()

    # -- Read custom libraries and store result to disk
    #    Custom Apps will be loaded with AppSettings.load_steam_apps
    dir_ids = set(AppSettings.user_app_directories.keys())
    for dir_id in dir_ids:
        scan_custom_libs(dir_id)

    try:
        # -- Read this machines Steam library
        app.steam.apps.read_steam_library()

        # -- Create a local copy of Steam Apps dict
        steam_apps = dict()
        steam_apps.update(app.steam.apps.steam_apps)

        # -- Remove Library Paths helper entry
        steam_apps.pop(app.steam.STEAM_LIBRARY_FOLDERS)
    except Exception as e:
        msg = f'Error getting Steam Lib: {e}'
        logging.error(msg)
        return json.dumps({'result': False, 'msg': msg})

    logging.debug('Acquiring OpenVR Dll locations for %s Steam Apps.', len(steam_apps.keys()))
    steam_apps = run_update_steam_apps(steam_apps)

    # -- Restore Mod settings cached on disk and add custom apps
    cached_steam_apps = AppSettings.load_steam_apps()

    # -- Restore cached selected installation paths for custom apps
    for app_id, cached_entry in cached_custom_apps.items():
        for mod in get_available_mods(dict()):
            if mod.DLL_LOC_KEY_SELECTED in cached_entry:
                cached_steam_apps[app_id][mod.DLL_LOC_KEY_SELECTED] = cached_entry[mod.DLL_LOC_KEY_SELECTED]

    for app_id, cached_entry in cached_steam_apps.items():
        if app_id in steam_apps:
            # -- Restore cached selected installation paths for steam apps
            for mod in get_available_mods(dict()):
                if mod.DLL_LOC_KEY_SELECTED in cached_entry:
                    steam_apps[app_id][mod.DLL_LOC_KEY_SELECTED] = cached_entry[mod.DLL_LOC_KEY_SELECTED]

            steam_apps.update(_load_steam_apps_with_mod_settings({app_id: steam_apps[app_id]}, scan_mod=True))

        # -- Add custom apps
        for dir_id in AppSettings.user_app_directories:
            if app_id.startswith(dir_id):
                steam_apps[app_id] = cached_entry

    # -- Cache updated SteamApps to disk
    try:
        save_steam_lib(steam_apps)
    except Exception as e:
        msg = f'Error saving Steam Lib data: {e}'
        logging.error(msg)
        return json.dumps({'result': False, 'msg': msg})

    logging.debug('Providing Front End with Steam Library [%s]', len(steam_apps.keys()))
    return json.dumps({'result': True, 'data': steam_apps})


@app.utils.capture_app_exceptions
def remove_custom_app_fn(app_dict: dict):
    custom_apps = AppSettings.load_custom_dir_apps()

    if app_dict.get('appid') not in custom_apps:
        return json.dumps({'result': False, 'msg': f'Could not find app with Id: {app_dict.get("appid")}'})

    entry = custom_apps.pop(app_dict.get('appid'))
    save_steam_lib(custom_apps)
    logging.debug('App entry: %s %s removed', entry.get('name'), entry.get('appid'))
    return json.dumps({'result': True, 'msg': f'App entry {entry.get("name")} {entry.get("appid")} removed.'})


@app.utils.capture_app_exceptions
def add_custom_app_fn(app_dict: dict):
    # -- Check path
    if app_dict.get('path') in (None, ''):
        return json.dumps({'result': False, 'msg': 'No valid path provided.'})

    path = Path(app_dict.get('path'))
    if not path.exists():
        return json.dumps({'result': False, 'msg': 'Provided path does not exist.'})

    user_apps = dict()
    for entry_id, entry in AppSettings.load_custom_dir_apps().items():
        if not entry_id.startswith(app.globals.USER_APP_PREFIX):
            continue

        user_apps[entry_id] = entry
        if Path(entry.get('path')) == path:
            return json.dumps({'result': False, 'msg': f'Entry already exists as '
                                                       f'{entry.get("name")}, Id: {entry_id}.'})

    # -- Create User Apps custom dir entry
    if app.globals.USER_APP_PREFIX not in AppSettings.user_app_directories:
        AppSettings.user_app_directories[app.globals.USER_APP_PREFIX] = app.globals.get_settings_dir().as_posix()
        AppSettings.save()

    # -- Create User App entry
    app_id = f'{app.globals.USER_APP_PREFIX}_{get_name_id(path.stem)}'
    manifest = create_custom_app(app_id, path, app_dict.get('name'))
    if not manifest:
        return json.dumps({'result': False, 'msg': f'No OpenVR dll or Executables found in: {path.as_posix()} or '
                                                   f'any sub directory.'})

    # -- Save custom app
    user_apps[app_id] = manifest
    result = AppSettings.save_custom_dir_apps(app.globals.USER_APP_PREFIX, reduce_steam_apps_for_export(user_apps))

    if result:
        return json.dumps({'result': result, 'msg': f'App entry {app_id} created.'})
    else:
        return json.dumps({'result': result, 'msg': f'Could not create user app settings.'})


@app.utils.capture_app_exceptions
def get_custom_dirs_fn():
    return AppSettings.user_app_directories


@app.utils.capture_app_exceptions
def remove_custom_dir_fn(dir_id: str):
    if dir_id not in AppSettings.user_app_directories:
        return json.dumps({'result': False, 'msg': f'Path id {dir_id} is unknown.'})

    entry = AppSettings.user_app_directories.pop(dir_id)
    result = AppSettings.remove_custom_dir_apps(dir_id)
    if not result:
        return json.dumps({'result': True, 'msg': f'Could not remove custom apps cache file.'})

    AppSettings.save()
    return json.dumps({'result': True, 'msg': f'Custom library {entry} removed.'})


@app.utils.capture_app_exceptions
def add_custom_dir_fn(path: str):
    path = Path(path)
    if not path.exists():
        return json.dumps({'result': False, 'msg': 'No valid path provided.'})

    for dir_id, usr_dir_path in AppSettings.user_app_directories.items():
        if Path(usr_dir_path) == path:
            return json.dumps({'result': False, 'msg': f'Directory already added {dir_id}: {path.as_posix()}'})

    new_dir_id = f'{app.globals.CUSTOM_APP_PREFIX}{get_name_id(path.as_posix())}'
    AppSettings.user_app_directories[new_dir_id] = path.as_posix()
    AppSettings.save()

    # -- Scan custom app dir
    result_dict = json.loads(scan_custom_libs(new_dir_id))
    if not result_dict['result']:
        return json.dumps(result_dict)

    return json.dumps({'result': True, 'msg': f'Added custom location {path.as_posix()}'})


@app.utils.capture_app_exceptions
def get_mod_dir_fn(mod_type: int):
    mod = app.mod.get_mod(dict(), mod_type)
    return str(WindowsPath(mod.get_source_dir()))


@app.utils.capture_app_exceptions
def set_mod_dir_fn(directory_str, mod_type: int):
    result = False

    # -- Reset
    if not directory_str:
        AppSettings.mod_data_dirs.pop(mod_type, None)
        app.mod.update_mod_data_dirs()
        result = True

    # -- Set
    if app.mod.check_mod_data_dir(Path(directory_str), mod_type):
        AppSettings.mod_data_dirs[mod_type] = str(WindowsPath(directory_str))
        AppSettings.save()
        result = True

    AppSettings.save()
    return json.dumps({'result': result})


@app.utils.capture_app_exceptions
def update_mod_fn(manifest: dict, mod_type: int = 0, write: bool = False):
    mod = app.mod.get_mod(manifest, mod_type)
    if not mod:
        return json.dumps({'result': False, 'msg': 'No Mod Type provided', 'manifest': manifest})

    if write:
        update_result = mod.write_updated_cfg()
    else:
        update_result = mod.update_from_disk()

    return json.dumps({'result': all((update_result, not mod.error)),
                       'msg': mod.error, 'manifest': mod.manifest})


@app.utils.capture_app_exceptions
def toggle_mod_install_fn(manifest: dict, mod_type: int = 0):
    mod = app.mod.get_mod(manifest, mod_type)
    mod_installed = mod.manifest.get(mod.VAR_NAMES['installed'], False)

    if not mod:
        return json.dumps({'result': False, 'msg': 'No Mod Type provided or could not get install state.',
                           'manifest': manifest})

    # -- Install
    if not mod_installed:
        install_result = mod.install()
        mod.update_from_disk()
        return json.dumps({'result': install_result, 'msg': mod.error, 'manifest': mod.manifest})
    # -- Uninstall
    elif mod_installed is True:
        uninstall_result = mod.uninstall()
        mod.update_from_disk()
        if uninstall_result:
            mod.manifest[mod.VAR_NAMES['version']] = str()
        return json.dumps({'result': uninstall_result, 'msg': mod.error, 'manifest': mod.manifest})


@app.utils.capture_app_exceptions
def reset_mod_settings_fn(manifest: dict, mod_type: int = 0):
    mod = app.mod.get_mod(manifest, mod_type)

    if mod.reset_settings():
        update_result = mod.write_updated_cfg()
        return json.dumps({'result': update_result, 'msg': mod.error, 'manifest': mod.manifest})

    return json.dumps({'result': False, 'msg': mod.error, 'manifest': mod.manifest})


@app.utils.capture_app_exceptions
def launch_app_fn(manifest: dict):
    app_id = manifest.get('appid')
    if not app_id:
        return json.dumps({'result': False, 'msg': 'Could not find valid Steam App ID'})

    cmd = f'explorer "steam://rungameid/{app_id}"'
    logging.info('Launching %s', cmd)

    subprocess.Popen(cmd)
    return json.dumps({'result': True, 'msg': f'Launched: {cmd}'})
