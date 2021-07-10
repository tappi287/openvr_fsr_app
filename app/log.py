import logging
import logging.config
from pathlib import Path

from .globals import APP_NAME, DEFAULT_LOG_LEVEL, get_log_file


def setup_logging(logger_name: str = APP_NAME):
    log_level = DEFAULT_LOG_LEVEL
    log_handlers = ['file', 'console']

    log_file_path: Path = get_log_file()

    log_conf = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'simple': {
                'format': '%(asctime)s %(thread)d-%(module)s %(levelname)s: %(message)s',
                'datefmt': '%d.%m.%Y %H:%M:%S'
                },
            'file_formatter': {
                'format': '%(asctime)s.%(msecs)03d %(thread)d-%(module)s %(funcName)s %(levelname)s: %(message)s',
                'datefmt': '%d.%m.%Y %H:%M:%S'
                },
            },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler', 'stream': 'ext://sys.stdout', 'formatter': 'simple',
                'level': log_level
                },
            'file': {
                'level'    : 'DEBUG', 'class': 'logging.handlers.RotatingFileHandler',
                'filename' : log_file_path.absolute().as_posix(), 'maxBytes': 415000, 'backupCount': 3,
                'formatter': 'file_formatter',
                },
            },
        'loggers': {
            logger_name: {
                'handlers': log_handlers, 'propagate': False, 'level': log_level,
                },
            # Module loggers
            '': {
                'handlers': log_handlers, 'propagate': False, 'level': log_level,
                }
            }
        }

    logging.config.dictConfig(log_conf)


def setup_logger(name):
    module_logger_name = f'{APP_NAME}.{name}'
    logging.getLogger(APP_NAME).info('Providing module with logger: %s', module_logger_name)
    return logging.getLogger(module_logger_name)


def reset_logging():
    manager = logging.root.manager
    manager.disabled = logging.NOTSET
    for logger in manager.loggerDict.values():
        if isinstance(logger, logging.Logger):
            logger.setLevel(logging.NOTSET)
            logger.propagate = True
            logger.disabled = False
            logger.filters.clear()
            handlers = logger.handlers.copy()
            for handler in handlers:
                # Copied from `logging.shutdown`.
                try:
                    handler.acquire()
                    handler.flush()
                    handler.close()
                except (OSError, ValueError):
                    pass
                finally:
                    handler.release()
                logger.removeHandler(handler)
