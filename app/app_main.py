import json
import logging
import subprocess
from pathlib import WindowsPath, Path

import eel
import gevent
import gevent.event

from .app_settings import AppSettings
from .fsr import FsrSettings, Fsr
from .globals import OPEN_VR_FSR_CFG
from .manifest_worker import ManifestWorker
from .runasadmin import run_as_admin
from .valve import steam

CLOSE_EVENT = gevent.event.Event()


def expose_main():
    pass


def request_close():
    logging.info('Received close request.')
    CLOSE_EVENT.set()
    eel.closeApp()(close_js_result)


def close_js_result(result):
    logging.info('JS close app result: %s', result)


@eel.expose
def close_request():
    request_close()


@eel.expose
def load_steam_lib():
    """ Load saved SteamApps from disk """
    steam_apps = AppSettings.load_steam_apps()
    return json.dumps({'result': True, 'data': steam_apps})


@eel.expose
def get_steam_lib():
    """ Refresh SteamLib and re-scan every app directory """
    logging.debug('Reading Steam Library')
    try:
        # -- Read this machines Steam library
        steam.apps.read_steam_library(find_open_vr=True)

        # -- Create a local copy of Steam Apps dict
        steam_apps = dict()
        steam_apps.update(steam.apps.steam_apps)

        # -- Remove Library Paths helper entry
        steam_apps.pop(steam.STEAM_LIBRARY_FOLDERS)
    except Exception as e:
        msg = f'Error getting Steam Lib: {e}'
        logging.error(msg)
        # for app_id, manifest in steam_apps.items():
        #     logging.debug(f'{app_id} {manifest.get("name")}')
        return json.dumps({'result': False, 'msg': msg})

    logging.debug('Acquiring OpenVR Dll locations for %s Steam Apps.', len(steam_apps.keys()))
    steam_apps = ManifestWorker.update_steam_apps(steam_apps)

    logging.debug('Providing Front End with Steam Library [%s]', len(steam_apps.keys()))
    return json.dumps({'result': True, 'data': steam_apps})


@eel.expose
def get_fsr_dir():
    if AppSettings.openvr_fsr_dir is not None and Path(AppSettings.openvr_fsr_dir).exists():
        open_fsr_dir = str(WindowsPath(AppSettings.openvr_fsr_dir))
        logging.info('Providing FSR Dir to FrontEnd: %s', open_fsr_dir)
        return open_fsr_dir


@eel.expose
def set_fsr_dir(directory_str):
    return json.dumps({'result': AppSettings.update_fsr_dir(directory_str)})


@eel.expose
def update_fsr(manifest: dict):
    fsr = Fsr(manifest)
    result = fsr.update_cfg()
    if result:
        logging.debug('Updated %s enabled %s renderScale %s sharpness %s', fsr.open_vr_dll.parent / OPEN_VR_FSR_CFG,
                      fsr.settings.enabled.value,
                      fsr.settings.renderScale.value,
                      fsr.settings.sharpness.value)
    else:
        logging.error('Error updating Fsr config!')
    return json.dumps({'result': result, 'msg': fsr.error})


@eel.expose
def install_fsr(manifest: dict):
    fsr = Fsr(manifest)
    return json.dumps({'result': fsr.install(), 'msg': fsr.error})


@eel.expose
def uninstall_fsr(manifest: dict):
    fsr = Fsr(manifest)
    return json.dumps({'result': fsr.uninstall(), 'msg': fsr.error})


@eel.expose
def launch_app(manifest: dict):
    app_id = manifest.get('appid')
    if not app_id:
        return json.dumps({'result': False, 'msg': 'Could not find valid Steam App ID'})

    # steam_path = Path(steam.apps.find_steam_location()) / 'steam.exe'
    # cmd = [str(WindowsPath(steam_path)), '-applaunch', app_id]
    cmd = f'explorer "steam://rungameid/{app_id}"'
    logging.info('Launching %s', cmd)

    subprocess.Popen(cmd)
    return json.dumps({'result': True, 'msg': f'Launched: {cmd}'})


@eel.expose
def re_run_admin():
    AppSettings.needs_admin = True
    AppSettings.save()

    if not run_as_admin():
        request_close()


@eel.expose
def reset_admin():
    AppSettings.needs_admin = False
    AppSettings.save()

    request_close()
