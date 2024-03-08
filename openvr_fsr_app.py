import logging
import os
import sys
import webbrowser
from pathlib import Path

import eel
import gevent
from gevent.hub import Hub

from app import expose_app_methods, CLOSE_EVENT
from app.app_main import close_request
from app.events import app_event_loop
from app.app_settings import AppSettings
from app.globals import FROZEN, get_version
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


def _start_in_browser():
    page = 'index.html'
    host = 'localhost'
    port = 8144
    eel.init('web')

    edge_cmd = f"{os.path.expandvars('%PROGRAMFILES(x86)%')}\\Microsoft\\Edge\\Application\\msedge.exe"
    start_url = f'http://{host}:{port}'

    try:
        app_module_prefs = getattr(AppSettings, 'app_preferences', dict()).get('appModules', list())
        if Path(edge_cmd).exists() and 'edge_preferred' in app_module_prefs:
            eel.start(page, mode='custom', host=host, port=port, block=False,
                      cmdline_args=[edge_cmd, '--profile-directory=Default', f'--app={start_url}'])
        else:
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


def start_eel():
    logging.info('\n\n\n')
    logging.info('#######################################################')
    logging.info('################ Starting APP               ###########')
    logging.info('#######################################################\n\n\n')

    if FROZEN:
        # Set Exception hook
        sys.excepthook = AppExceptionHook.exception_hook
        register_gevent_error_handler(AppExceptionHook.gevent_error_handler)

    AppSettings.load()

    # This will ask for and re-run with admin rights
    # if setting needs_admin set.
    if AppSettings.needs_admin and not run_as_admin():
        return

    """
        THIS WILL DISABLE ctypes support! But it will make sure launching an executable
        or basically any executable that is loading DLLs will work.
    """
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetDllDirectoryA(None)
    """
        //
    """
    _start_in_browser()
    gevent.sleep(0.5)
    if AppExceptionHook.event.is_set():
        logging.error('Exception making app available in browser. Aborting.')
        CLOSE_EVENT.set()
        raise RuntimeError(AppExceptionHook.gui_msg)

    # -- Run until window/tab closed
    while not CLOSE_EVENT.is_set():
        CLOSE_EVENT.wait(timeout=1)

        # --- Event loop ---
        app_event_loop()

        # Capture exception events
        AppExceptionHook.exception_event_loop()

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
