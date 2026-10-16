import logging
import os

from atmoswing_api import config

# Logger of the package: modules log through logging.getLogger(__name__), whose
# messages propagate to it. Third-party loggers (h5py, httpx, ...) are not affected.
PACKAGE_LOGGER = "atmoswing_api"

_FORMAT = "%(asctime)s - %(levelname)s - %(name)s - %(message)s"


def configure_logging(settings: config.Settings):
    """
    Configure the package logger: messages go to the terminal, and errors (or
    everything in debug mode) also to settings.log_file when it is set. Calling
    it again replaces the previous configuration, so handlers never pile up.
    """
    logger = logging.getLogger(PACKAGE_LOGGER)
    for handler in list(logger.handlers):
        logger.removeHandler(handler)
        handler.close()

    logger.setLevel(logging.DEBUG if settings.debug else logging.INFO)
    # The handlers below are the only ones: do not duplicate messages in the root logger
    logger.propagate = False
    formatter = logging.Formatter(_FORMAT)

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)

    if settings.log_file:
        log_dir = os.path.dirname(settings.log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
        file_handler = logging.FileHandler(settings.log_file)
        file_handler.setLevel(logging.DEBUG if settings.debug else logging.ERROR)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
