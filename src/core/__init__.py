import os
from pathlib import Path
import logging
from logging.handlers import RotatingFileHandler
from kivymd.app import MDApp
from .base import SessionManager  # for compatibility in other classes but will have to clean later on
from .base import get_app_home_directory
from .config_parser import ConfigurationManager


APP_NAME = "Relo Downloader"
THEMES = ["Light", "Dark", "Black"]


def get_running_app():
    return MDApp.get_running_app()


# set logger
log_file = "app.log"
log_path = Path(get_app_home_directory()).joinpath(log_file)
logger = logging.getLogger(APP_NAME)
logger.setLevel(logging.INFO)
handler = RotatingFileHandler(log_path, maxBytes=10485760, backupCount=10)
formatter = logging.Formatter("%(asctime)s- %(name)s - %(levelname)s - %(message)s")
handler.setFormatter(formatter)
logger.handlers.clear()
logger.addHandler(handler)

# init config
config = ConfigurationManager(logger=logger)
