import logging
from datetime import datetime
from pathlib import Path
from utils.config_manager import ConfigManager


def setup_logger():
    config_manager = ConfigManager()
    config = config_manager.get_logging_config()

    # 设置日志级别
    level = config.get("level", "INFO").upper()
    level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }
    log_level = level_map.get(level, logging.INFO)

    # 创建 logs 目录
    logs_dir = Path(".logs")
    logs_dir.mkdir(exist_ok=True)

    # 设置日志格式
    formatter = logging.Formatter(
        "%(asctime)s|%(levelname)s|%(filename)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 获取或创建 logger
    logger = logging.getLogger("pyMonitor")
    logger.setLevel(log_level)

    # 清除现有的处理器，避免重复添加
    logger.handlers.clear()

    # 根据配置决定是否添加处理器
    if config.get("log_to_file", True):
        # 创建按日期命名的日志文件
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

    return logger


logger = setup_logger()
