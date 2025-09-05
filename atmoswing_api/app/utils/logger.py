import logging
import os
from atmoswing_api import config

def create_logger():
    """
    Create and configure a logger that logs errors to a file and info messages to the terminal.
    """
    # Ensure the directory for the log file exists
    log_file_path = config.Settings().data_dir + '/app.log'
    os.makedirs(os.path.dirname(log_file_path), exist_ok=True)

    # Debug mode
    debug_mode = config.Settings().debug
    if debug_mode:
        log_level = logging.DEBUG
        log_level_file = logging.DEBUG
        log_level_console = logging.DEBUG
    else:
        log_level = logging.INFO
        log_level_file = logging.ERROR
        log_level_console = logging.INFO

    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(log_level)

    # File handler for errors
    file_handler = logging.FileHandler(log_file_path)
    file_handler.setLevel(log_level_file)  # Log only errors and above to the file
    file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(file_formatter)

    # Stream handler for terminal output
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(log_level_console)  # Log info and above to the terminal
    stream_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
    stream_handler.setFormatter(stream_formatter)

    # Add handlers to the logger
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)

    return logger

def get_logger():
    """
    Retrieve the configured root logger.
    """
    return logging.getLogger()
