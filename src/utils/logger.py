import logging
from datetime import datetime
from pathlib import Path

_logger_instance = None


def setup_logger():
    global _logger_instance

    if _logger_instance is not None:
        return _logger_instance

    from utils.config_manager import ConfigManager

    config_manager = ConfigManager()
    config = config_manager.get_logging_config()

    level = config.get("level", "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = level_map.get(level, logging.INFO)

    logs_dir = Path(".logs")
    logs_dir.mkdir(exist_ok=True)

    formatter = logging.Formatter(
        "%(asctime)s|%(levelname)s|%(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    logger = logging.getLogger("pyMonitor")
    logger.setLevel(log_level)
    logger.handlers.clear()

    if config.get("log_to_file", True):
        log_filename = f"system_monitor_{datetime.now().strftime('%Y%m%d')}.log"
        log_file = logs_dir / log_filename

        file_handler = logging.FileHandler(log_file, encoding="utf-8", mode="a")
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    if config.get("log_to_console", True):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

    _logger_instance = logger
    return _logger_instance


logger = setup_logger()
