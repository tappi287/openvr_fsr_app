import logging
import os
import sys
import time
import webbrowser
from pathlib import Path

import eel
import gevent
from gevent.hub import Hub

from app import expose_app_methods, CLOSE_EVENT
from app.app_main import close_request
from app.app_event_loop import app_event_loop
from app.app_settings import AppSettings
from app.globals import FROZEN, get_version, get_current_modules_dir
from app.log import setup_logging
from app.util.runasadmin import run_as_admin
from app.util.utils import AppExceptionHook

# -- Make sure eel methods are exposed at start-up
expose_app_methods()

# -- Setup logging
setup_logging()


IGNORE_ERROR = Hub.SYSTEM_ERROR + Hub.NOT_ERROR


def register_gevent_error_handler(error_handler):

    Hub._origin_handle_error = Hub.handle_error

    def custom_handle_error(self, context, e_type, value, tb):
        if issubclass(e_type, IGNORE_ERROR):
            return
        logging.error('Got error from greenlet: %s %s %s %s', context, e_type, value, tb)
        error_handler(context, (e_type, value, tb))

        self._origin_handle_error(context, e_type, value, tb)

    Hub.handle_error = custom_handle_error
    logging.debug('Registered gevent error handler')


def _start_in_browser(npm_serve=True):
    page = 'index.html'
    host = 'localhost'
    port = 8144

    if npm_serve:
        # Dev env with npm run serve
        page = {'port': 8080}
        url_port = page.get('port')
        eel.init(Path(get_current_modules_dir()).joinpath('src').as_posix())
    else:
        # Frozen or npm run build
        url_port = port
        eel.init(Path(get_current_modules_dir()).joinpath('web').as_posix())

    edge_cmd = f"{os.path.expandvars('%PROGRAMFILES(x86)%')}\\Microsoft\\Edge\\Application\\msedge.exe"
    start_url = f'http://{host}:{url_port}'
    logging.debug(f'Preparing Browser start: {start_url}/{page}')
    if Path(edge_cmd).exists():
        logging.debug(f'Found Edge: {edge_cmd}')
    else:
        logging.debug(f'Edge not found: {edge_cmd}')

    try:
        app_module_prefs = getattr(AppSettings, 'app_preferences', dict()).get('appModules', list())
        if Path(edge_cmd).exists() and 'edge_preferred' in app_module_prefs:
            logging.debug('Starting in Edge.')
            eel.start(page, mode='custom', host=host, port=port, block=False,
                      cmdline_args=[edge_cmd, '--profile-directory=Default', f'--app={start_url}'])
        else:
            logging.debug('Starting in Chrome.')
            eel.start(page, host=host, port=port, block=False, close_callback=close_request)
    except EnvironmentError:
        # If Chrome isn't found, fallback to Microsoft Chromium Edge
        if Path(edge_cmd).exists():
            logging.info('Falling back to Edge Browser')
            eel.start(page, mode='custom', host=host, port=port, block=False,
                      cmdline_args=[edge_cmd, '--profile-directory=Default', f'--app={start_url}'])
        # Fallback to opening a regular browser window
        else:
            logging.info('Falling back to default Web Browser')
            eel.start(page, mode=None, app_mode=False, host=host, port=port, block=False)
            # Open system default web browser
            webbrowser.open_new(start_url)
    logging.debug('Browser Start finished')


def start_eel():
    logging.info('\n\n\n')
    logging.info('#######################################################')
    logging.info('################ Starting APP               ###########')
    logging.info('#######################################################')

    if FROZEN:
        # Set Exception hook
        sys.excepthook = AppExceptionHook.exception_hook
        register_gevent_error_handler(AppExceptionHook.gevent_error_handler)

    AppSettings.load()
    logging.debug('App-Settings loaded')

    # This will ask for and re-run with admin rights
    # if setting needs_admin set.
    if AppSettings.needs_admin and not run_as_admin():
        return

    _start_in_browser(not FROZEN)
    gevent.sleep(0.5)
    if AppExceptionHook.event.is_set():
        logging.error('Exception making app available in browser. Aborting.')
        CLOSE_EVENT.set()
        raise RuntimeError(AppExceptionHook.gui_msg)

    # -- Run until window/tab closed
    logging.debug('Entering event loop')
    start_time = time.time()
    while not CLOSE_EVENT.is_set():
        # --- Event loop ---
        app_event_loop(start_time)

        # Capture exception events
        AppExceptionHook.exception_event_loop()

        CLOSE_EVENT.wait(timeout=1)

    # -- Shutdown Greenlets
    # logging.debug('Shutting down Greenlets.')
    # gevent.joinall((cg, hg, rg), timeout=15.0, raise_error=True)
    AppSettings.previous_version = get_version()
    AppSettings.save()

    # -- Shutdown logging
    logging.info('\n\n\n')
    logging.info('#######################################################')
    logging.info('################ APP SHUTDOWN               ###########')
    logging.info('#######################################################\n\n\n')
    logging.shutdown()


if __name__ == '__main__':
    start_eel()
