import logging
from datetime import datetime
import os


def setup_logger(name: str = "twitter_scraper", log_file: str = None, level: int = logging.INFO):
    """Функция для настройки логирования"""
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # Удаляем существующие обработчики, чтобы не было дублирования
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Консольный обработчик
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # Файловый обработчик
    if log_file is None:
        log_dir = "logs"
        os.makedirs(log_dir, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = f"logs/twitter_scraper_{timestamp}.log"

    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger