import logging
from typing import Optional

import eel
import gevent
import gevent.event


class AppBaseEvent:
    @classmethod
    def get_nowait(cls) -> Optional[gevent.event.AsyncResult]:
        if hasattr(cls, 'result'):
            try:
                return cls.result.get_nowait()
            except gevent.Timeout:
                pass

    @classmethod
    def reset(cls):
        if hasattr(cls, 'event') and hasattr(cls, 'result'):
            cls.event.clear()
            cls.result = gevent.event.AsyncResult()


class ProgressEvent(AppBaseEvent):
    event = gevent.event.Event()
    result = gevent.event.AsyncResult()

    @classmethod
    def set(cls, value):
        cls.result.set(value)


def progress_update(message):
    ProgressEvent.set(message)


def app_event_loop():
    progress_event = ProgressEvent.get_nowait()
    if progress_event:
        logging.debug('Progress event callback to FrontEnd: %s', progress_event)
        eel.update_progress(progress_event)
        ProgressEvent.reset()
