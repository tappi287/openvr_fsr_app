import json
import logging
from pathlib import Path

import app.util.utils
from app.app_fn import reduce_steam_apps_for_export
from app.app_settings import AppSettings
from app.util.custom_app import scan_custom_library


@app.utils.capture_app_exceptions
def scan_custom_libs_fn(dir_id: str):
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