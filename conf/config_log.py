import logging, os
from datetime import datetime


def setup_logger(name="job_project"):
    base_log_path = os.environ.get("COLLECTOR_LOG_FILE")
    today = datetime.now().strftime("%Y%m%d")
    log_file = f"{base_log_path}_{today}.log"

    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)

    if logger.handlers:
        return logger  # 중복 핸들러 방지

    formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s",
        "%Y-%m-%d %H:%M:%S"
    )

    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.propagate = False

    return logger
