from typing import Optional

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
