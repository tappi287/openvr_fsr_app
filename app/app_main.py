import logging

import eel
import gevent.event

from . import app_fn
from .app_settings import AppSettings
from app.util.runasadmin import run_as_admin

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
    return app_fn.load_steam_lib_fn()


@eel.expose
def scan_app_lib():
    """ Refresh SteamLib and re-scan every app directory """
    return app_fn.scan_app_lib_fn()


@eel.expose
def save_steam_lib(steam_apps):
    return app_fn.save_steam_lib(steam_apps)


@eel.expose
def remove_custom_app(app: dict):
    return app_fn.remove_custom_app_fn(app)


@eel.expose
def add_custom_app(app: dict):
    return app_fn.add_custom_app_fn(app)


@eel.expose
def add_custom_dir(path: str):
    return app_fn.add_custom_dir_fn(path)


@eel.expose
def remove_custom_dir(dir_id: str):
    return app_fn.remove_custom_dir_fn(dir_id)


@eel.expose
def get_custom_dirs():
    return app_fn.get_custom_dirs_fn()


@eel.expose
def get_mod_dir(mod_type):
    return app_fn.get_mod_dir_fn(mod_type)


@eel.expose
def set_mod_dir(directory_str, mod_type):
    return app_fn.set_mod_dir_fn(directory_str, mod_type)


@eel.expose
def update_mod(manifest: dict, mod_type: int = 0, write: bool = False):
    return app_fn.update_mod_fn(manifest, mod_type, write)


@eel.expose
def toggle_mod_install(manifest: dict, mod_type: int = 0):
    return app_fn.toggle_mod_install_fn(manifest, mod_type)


@eel.expose
def reset_mod_settings(manifest: dict, mod_type: int = 0):
    return app_fn.reset_mod_settings_fn(manifest, mod_type)


@eel.expose
def launch_app(manifest: dict):
    return app_fn.launch_app_fn(manifest)


@eel.expose
def get_current_fsr_version():
    return AppSettings.current_fsr_version


@eel.expose
def get_current_foveated_version():
    return AppSettings.current_foveated_version


@eel.expose
def get_current_vrperfkit_version():
    return AppSettings.current_vrperfkit_version


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
