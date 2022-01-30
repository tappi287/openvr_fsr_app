import logging
import platform
import sys
import webbrowser

import eel

from app import expose_app_methods, CLOSE_EVENT
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


def start_eel():
    logging.info('\n\n\n')
    logging.info('#######################################################')
    logging.info('################ Starting APP               ###########')
    logging.info('#######################################################\n\n\n')

    if FROZEN:
        # Set Exception hook
        sys.excepthook = AppExceptionHook.exception_hook

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
    page = 'index.html'
    host = 'localhost'
    port = 8144
    eel.init('web')

    # TODO: fetch OSError port in use
    try:
        eel.start(page, host=host, port=port, block=False)
    except EnvironmentError:
        # If Chrome isn't found, fallback to Microsoft Edge on Win10 or greater
        edge_failed = False
        if sys.platform in ['win32', 'win64'] and int(platform.release()) >= 10:
            try:
                eel.start(page, mode='edge', host=host, port=port, block=False)
            except Exception as e:
                logging.error(e)
                edge_failed = True
        # Fallback to opening a regular browser window
        else:
            edge_failed = True

        if edge_failed:
            eel.start(page, mode=None, app_mode=False, host=host, port=port, block=False)
            # Open system default web browser
            webbrowser.open_new(f'http://{host}:{port}')

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
