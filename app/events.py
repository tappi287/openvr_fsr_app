import logging
from typing import Optional

import gevent
import gevent.event
from gevent.hub import Hub


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
