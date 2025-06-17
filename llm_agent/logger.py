import logging
import os
from datetime import datetime

LOGS_DIR = "logs"
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

log_filename = datetime.now().strftime("run_%Y%m%d_%H%M%S.log")
log_filepath = os.path.join(LOGS_DIR, log_filename)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.FileHandler(log_filepath, "w", "utf-8")],
)

file_handler = logging.FileHandler(log_filepath, "w", "utf-8")
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter(
    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
file_handler.setFormatter(formatter)

logger = logging.getLogger(__name__)
logger.addHandler(file_handler)


def log(message: str, level=logging.INFO):
    logger.log(level, message)


def log_to_run(message: str):
    with open("run.log", "a", encoding="utf-8") as f:
        f.write(message + "\n") 