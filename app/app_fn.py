import json
import logging
import subprocess
from pathlib import WindowsPath, Path

import app
from .app_settings import AppSettings
from .manifest_worker import ManifestWorker
from .openvr_mod import get_mod, get_available_mods


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
        reduced_dict[app_id]['openVr'] = entry.get('openVr')
        reduced_dict[app_id]['SizeOnDisk'] = entry.get('SizeOnDisk')
        reduced_dict[app_id]['appid'] = entry.get('appid')

        # Mod specific data
        if entry.get('openVr'):
            for mod in get_available_mods(entry):
                reduced_dict[app_id][mod.VAR_NAMES['settings']] = mod.settings.to_js(export=True)
                reduced_dict[app_id][mod.VAR_NAMES['installed']] = entry.get(mod.VAR_NAMES['installed'], False)
                reduced_dict[app_id][mod.VAR_NAMES['version']] = entry.get(mod.VAR_NAMES['version'], '')
            reduced_dict[app_id]['fsr_compatible'] = entry.get('fsr_compatible', True)

    return reduced_dict


@app.utils.capture_app_exceptions
def _load_steam_apps_with_mod_settings(steam_apps, flag_as_user_app=False):
    """ Add or restore complete settings entries """
    for app_id, entry in steam_apps.items():
        entry['userApp'] = flag_as_user_app

        if entry.get('openVr'):
            for mod in get_available_mods(entry):
                entry[mod.VAR_NAMES['settings']] = mod.settings.to_js(export=False)

    return steam_apps


@app.utils.capture_app_exceptions
def save_steam_lib(steam_apps):
    logging.info('Updating SteamApp disk cache.')

    # -- Save disk cache without User Apps
    #    and update AppSettings User App entries
    remove_ids = set()
    for app_id, entry in steam_apps.items():
        if not app_id:
            continue
        if entry.get('_showDetails'):
            entry.pop('_showDetails')
        if entry.get('userApp', False) is True or app_id.startswith(app.globals.USER_APP_PREFIX):
            remove_ids.add(app_id)

    user_apps = dict()
    for app_id in remove_ids:
        user_entry = steam_apps.pop(app_id)
        user_apps[app_id] = user_entry

    AppSettings.user_apps = reduce_steam_apps_for_export(user_apps)
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

    # -- Add User Apps
    steam_apps.update(_load_steam_apps_with_mod_settings(AppSettings.user_apps, True))

    return json.dumps({'result': True, 'data': steam_apps, 'reScanRequired': re_scan_required})


@app.utils.capture_app_exceptions
def get_steam_lib_fn():
    """ Refresh SteamLib and re-scan every app directory """
    logging.debug('Reading Steam Library')
    try:
        # -- Read this machines Steam library
        app.valve.steam.apps.read_steam_library(find_open_vr=True)

        # -- Create a local copy of Steam Apps dict
        steam_apps = dict()
        steam_apps.update(app.valve.steam.apps.steam_apps)

        # -- Remove Library Paths helper entry
        steam_apps.pop(app.valve.steam.STEAM_LIBRARY_FOLDERS)
    except Exception as e:
        msg = f'Error getting Steam Lib: {e}'
        logging.error(msg)
        # for app_id, manifest in steam_apps.items():
        #     logging.debug(f'{app_id} {manifest.get("name")}')
        return json.dumps({'result': False, 'msg': msg})

    logging.debug('Acquiring OpenVR Dll locations for %s Steam Apps.', len(steam_apps.keys()))
    steam_apps = ManifestWorker.update_steam_apps(steam_apps)

    # -- Restore FSR settings cached on disk and determine if cache and disk are out of sync
    cached_steam_apps = _load_steam_apps_with_mod_settings(AppSettings.load_steam_apps())
    for app_id, entry in cached_steam_apps.items():
        if app_id in steam_apps:
            steam_apps[app_id]['openVrDllPathsSelected'] = entry['openVrDllPathsSelected']

    # -- Add User Apps
    AppSettings.load()
    steam_apps.update(AppSettings.user_apps)

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
    if app_dict.get('appid') not in AppSettings.user_apps:
        return json.dumps({'result': False, 'msg': f'Could not find app with Id: {app_dict.get("appid")}'})

    entry = AppSettings.user_apps.pop(app_dict.get('appid'))
    AppSettings.save()
    logging.debug('App entry: %s %s removed', entry.get('name'), entry.get('appid'))
    return json.dumps({'result': True, 'msg': f'App entry {entry.get("name")} {entry.get("appid")} created.'})


@app.utils.capture_app_exceptions
def add_custom_app_fn(app_dict: dict):
    # -- Check path
    if app_dict.get('path') in (None, ''):
        return json.dumps({'result': False, 'msg': 'No valid path provided.'})

    path = Path(app_dict.get('path'))
    if not path.exists():
        return json.dumps({'result': False, 'msg': 'Provided path does not exist.'})

    for app_id, entry in AppSettings.user_apps.items():
        if entry.get('path') == path.as_posix():
            return json.dumps({'result': False, 'msg': f'Entry already exists as '
                                                       f'{entry.get("name")}, Id: {app_id}.'})

    # -- Check and find OpenVR
    openvr_paths = [p for p in ManifestWorker.find_open_vr_dll(path)]
    if not openvr_paths:
        return json.dumps({'result': False, 'msg': f'No OpenVR dll found in: {path.as_posix()} or any sub directory.'})

    # -- Create User App entry
    AppSettings.user_app_counter += 1
    app_id = f'{app.globals.USER_APP_PREFIX}{AppSettings.user_app_counter:03d}'
    logging.debug('Creating User App entry %s', app_id)
    manifest = {
        'appid': app_id,
        "name": app_dict.get('name', app_id),
        'path': path.as_posix(),
        'openVrDllPaths': [p.as_posix() for p in openvr_paths],
        'openVrDllPathsSelected': [p.as_posix() for p in openvr_paths],
        'openVr': True,
        'sizeGb': 0, 'SizeOnDisk': 0,
        'userApp': True,
    }

    # -- Add Mod specific data
    for mod in get_available_mods(manifest):
        installed_results = list()
        for p in openvr_paths:
            installed_results.append(mod.settings.read_from_cfg(p.parent))
        manifest[mod.VAR_NAMES['settings']] = mod.settings.to_js(export=True)
        manifest[mod.VAR_NAMES['installed']] = any(installed_results)
        manifest[mod.VAR_NAMES['version']] = mod.get_version()

    AppSettings.user_apps[app_id] = manifest
    AppSettings.save()

    return json.dumps({'result': True, 'msg': f'App entry {app_id} created.'})


@app.utils.capture_app_exceptions
def get_fsr_dir_fn():
    if AppSettings.openvr_fsr_dir is not None and Path(AppSettings.openvr_fsr_dir).exists():
        open_fsr_dir = str(WindowsPath(AppSettings.openvr_fsr_dir))
        logging.info('Providing FSR Dir to FrontEnd: %s', open_fsr_dir)
        return open_fsr_dir


@app.utils.capture_app_exceptions
def set_fsr_dir_fn(directory_str):
    if not directory_str:
        directory_str = str(WindowsPath(app.globals.get_data_dir() / 'openvr_fsr'))
    return json.dumps({'result': AppSettings.update_fsr_dir(directory_str)})


@app.utils.capture_app_exceptions
def update_mod_fn(manifest: dict, mod_type: int = 0, write: bool = False):
    mod = get_mod(manifest, mod_type)
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
    mod = get_mod(manifest, mod_type)
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
        if uninstall_result:
            mod.manifest[mod.VAR_NAMES['version']] = str()
        return json.dumps({'result': uninstall_result, 'msg': mod.error, 'manifest': mod.manifest})


@app.utils.capture_app_exceptions
def reset_mod_settings_fn(manifest: dict, mod_type: int = 0):
    mod = get_mod(manifest, mod_type)

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
