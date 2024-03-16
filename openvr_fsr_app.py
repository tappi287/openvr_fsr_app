import logging
import sys
import time

import gevent

from app import expose_app_methods, CLOSE_EVENT
from app.app_event_loop import app_event_loop
from app.app_settings import AppSettings
from app.events import register_gevent_error_handler
from app.globals import FROZEN, get_version
from app.log import setup_logging
from app.start import start_in_browser
from app.util.runasadmin import run_as_admin
from app.util.utils import AppExceptionHook

# -- Make sure eel methods are exposed at start-up
expose_app_methods()

# -- Setup logging
setup_logging()

SEP = "#######################################################"
N_SEP = "\n\n\n"


def start_eel():
    logging.info(N_SEP)
    logging.info(SEP)
    logging.info('################ Starting APP               ###########')
    logging.info(SEP)

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

    start_in_browser(not FROZEN)
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
    logging.info(SEP)
    logging.info('################ APP SHUTDOWN               ###########')
    logging.info(SEP + N_SEP)
    logging.shutdown()


if __name__ == '__main__':
    start_eel()
