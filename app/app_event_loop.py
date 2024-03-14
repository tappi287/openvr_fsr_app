import logging
import time

import eel

from app import CLOSE_EVENT, BROWSER_ALIVE
from app.events import ProgressEvent

BROWSER_TIMEOUT = 10.0


def app_event_loop(start_time: float):
    progress_event = ProgressEvent.get_nowait()
    if progress_event:
        logging.debug('Progress event callback to FrontEnd: %s', progress_event)
        if hasattr(eel, 'update_progress'):
            eel.update_progress(progress_event)
        ProgressEvent.reset()

    if time.time() - start_time > BROWSER_TIMEOUT and not BROWSER_ALIVE.is_set():
        logging.fatal(f'Could not reach Browser or FrontEnd after {BROWSER_TIMEOUT}s. App will exit.')
        CLOSE_EVENT.set()

    if BROWSER_ALIVE.is_set():
        logging.debug(f'Browser/FrontEnd reported to be alive in {time.time() - start_time:.2f}s')
        BROWSER_ALIVE.clear()
