import logging
from pathlib import Path
from typing import Optional

import app
import app.mod
from app.util.manifest_worker import ManifestWorker, run_update_steam_apps
from app.util.utils import get_name_id


def create_custom_app(app_id: str, path: Path, name: str = None, scan=True) -> Optional[dict]:
    if not name:
        name = path.stem

    # -- Create User App entry
    manifest = {
        'appid': app_id,
        "name": name,
        'path': path.as_posix(),
        'openVr': False,
        'sizeGb': 0, 'SizeOnDisk': 0,
        'userApp': True,
    }

    # -- Check and find OpenVR / Executables
    if scan:
        openvr_paths = [p for p in ManifestWorker.find_open_vr_dll(path)]
        executable_path_ls = [p for p in ManifestWorker.find_executables(path)]
        if not openvr_paths and not executable_path_ls:
            return

        manifest.update({
            'openVrDllPaths': [p.as_posix() for p in openvr_paths],
            'openVr': True if openvr_paths else False,
            'openVrDllPathsSelected': [p.as_posix() for p in openvr_paths],
            'executablePaths': [p.as_posix() for p in executable_path_ls],
            'executablePathsSelected': [p.as_posix() for p in executable_path_ls],
        })

        # -- Add Mod specific data
        for mod in app.mod.get_available_mods(manifest):
            installed_results = list()
            for p in openvr_paths:
                installed_results.append(mod.settings.read_from_cfg(p.parent))
            manifest[mod.VAR_NAMES['settings']] = mod.settings.to_js(export=True)
            manifest[mod.VAR_NAMES['installed']] = any(installed_results)
            manifest[mod.VAR_NAMES['version']] = mod.get_version()

    logging.debug('Creating User App entry %s', app_id)
    return manifest


def scan_custom_library(dir_id: str, path: Path):
    custom_apps = dict()

    for app_dir in path.glob('*'):
        if not app_dir.is_dir():
            continue
        app_id = f'{dir_id}_{get_name_id(app_dir.as_posix())}'
        custom_app = create_custom_app(app_id, app_dir, app_dir.stem, scan=False)
        if not custom_app:
            continue
        custom_apps[app_id] = custom_app

    if custom_apps:
        # -- Scan
        custom_apps = run_update_steam_apps(custom_apps)

    # -- Remove empty entries
    remove_ids = set()
    for app_id, entry in custom_apps.items():
        if not entry['openVrDllPaths'] and not entry['executablePaths']:
            remove_ids.add(app_id)
    for app_id in remove_ids:
        custom_apps.pop(app_id)

    return custom_apps
