import logging

import eel
import gevent.event

from . import app_fn
from .app_settings import AppSettings
from .runasadmin import run_as_admin
from .utils import capture_app_exceptions

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
def get_steam_lib():
    """ Refresh SteamLib and re-scan every app directory """
    return app_fn.get_steam_lib_fn()


@eel.expose
def remove_custom_app(app: dict):
    return app_fn.remove_custom_app_fn(app)


@eel.expose
def add_custom_app(app: dict):
    return app_fn.add_custom_app_fn(app)


@eel.expose
def get_fsr_dir():
    return app_fn.get_fsr_dir_fn()


@eel.expose
def set_fsr_dir(directory_str):
    return app_fn.set_fsr_dir_fn(directory_str)


@eel.expose
def update_fsr(manifest: dict):
    return app_fn.update_fsr_fn(manifest)


@eel.expose
def install_fsr(manifest: dict):
    return app_fn.install_fsr_fn(manifest)


@eel.expose
def uninstall_fsr(manifest: dict):
    return app_fn.uninstall_fsr_fn(manifest)


@eel.expose
def launch_app(manifest: dict):
    return app_fn.launch_app_fn(manifest)


@eel.expose
def get_current_fsr_version():
    return AppSettings.current_fsr_version


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
