import logging
import pytest
from atmoswing_api import config
from atmoswing_api.app.utils.logger import configure_logging, PACKAGE_LOGGER


@pytest.fixture(autouse=True)
def restore_logging():
    yield
    # Close the file handlers of the tests and restore the default configuration
    configure_logging(config.Settings(log_file=None, debug=False))


def handler_types():
    return [type(h) for h in logging.getLogger(PACKAGE_LOGGER).handlers]


def test_handlers_do_not_pile_up():
    for _ in range(3):
        configure_logging(config.Settings(log_file=None))
    assert handler_types() == [logging.StreamHandler]


def test_no_log_file_by_default(tmp_path):
    configure_logging(config.Settings(data_dir=str(tmp_path), log_file=None))
    assert handler_types() == [logging.StreamHandler]
    assert not (tmp_path / "app.log").exists()


@pytest.mark.parametrize("debug, logged", [
    (False, ["error message"]),
    (True, ["debug message", "info message", "error message"]),
])
def test_log_file(tmp_path, debug, logged):
    log_file = tmp_path / "logs" / "app.log"
    configure_logging(config.Settings(log_file=str(log_file), debug=debug))

    # Module loggers propagate to the package logger
    module_logger = logging.getLogger("atmoswing_api.app.routes.common")
    module_logger.debug("debug message")
    module_logger.info("info message")
    module_logger.error("error message")
    for handler in logging.getLogger(PACKAGE_LOGGER).handlers:
        handler.flush()

    content = log_file.read_text()
    for message in ["debug message", "info message", "error message"]:
        assert (message in content) == (message in logged)
    assert "atmoswing_api.app.routes.common" in content


def test_debug_does_not_affect_other_loggers():
    root_level = logging.getLogger().level
    configure_logging(config.Settings(log_file=None, debug=True))
    assert logging.getLogger(PACKAGE_LOGGER).level == logging.DEBUG
    assert logging.getLogger().level == root_level
    assert logging.getLogger("h5py").getEffectiveLevel() > logging.DEBUG
