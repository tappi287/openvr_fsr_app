import logging
import os
import sys
import time

import eel

from app import CLOSE_EVENT, BROWSER_ALIVE
from app.app_settings import AppSettings, BrowserSettings
from app.events import ProgressEvent
from app.globals import FROZEN

BROWSER_TIMEOUT = 10.0


def _restart_in_another_browser():
    BrowserSettings.set_current_browser_unavailable()
    AppSettings.browser_settings = BrowserSettings.to_settings()
    AppSettings.save()

    if FROZEN:
        logging.info('Restarting in another browser...')
        CLOSE_EVENT.set()
        logging.shutdown()
        os.execv(sys.executable, sys.argv)


def app_event_loop(start_time: float):
    progress_event = ProgressEvent.get_nowait()
    if progress_event:
        logging.debug('Progress event callback to FrontEnd: %s', progress_event)
        if hasattr(eel, 'update_progress'):
            eel.update_progress(progress_event)
        ProgressEvent.reset()

    # -- Browser App Mode / Window Health check
    if time.time() - start_time > BROWSER_TIMEOUT and not BROWSER_ALIVE.is_set():
        logging.fatal(f'Could not reach Browser or FrontEnd after {BROWSER_TIMEOUT}s.')
        _restart_in_another_browser()
    elif BROWSER_ALIVE.is_set():
        logging.debug(f'Browser/FrontEnd reported to be alive in {time.time() - start_time:.2f}s')
        BROWSER_ALIVE.clear()
