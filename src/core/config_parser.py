import os
import configparser
from src.core.base import get_app_home_directory


class ConfigurationManager:
    """
    Handles loading, saving, and updating configuration settings
    """
    DEFAULTS = {
        "Theme": {
            "theme_name": "Dark",
            "theme_color": "#99b2cc"
        },
        "Font": {
            "font_size": 17,
            "small_font_size": 13,
            "sub_header_size": 22,
            "headers_font_size": 26,
            "more_headers_font_size": 32,
            "make_all_text_bold": False
        },
        "Neon": {
            "on": False,
            "effect_size": 4,
            "elevation": 2
        },
        "Downloads": {
            "location": "Downloads",
            "simultaneous_downloads": 4,
            "audio_quality": "128kbps",
            "video_quality": "720p",
            "download_chunk_size": 1048576 # 1 mb
        },
        "Albums": {
            "max_pages": 50
        }
    }

    def __init__(self, logger=None):
        self.logger = logger
        self.config = configparser.ConfigParser()
        self.config_path = os.path.join(get_app_home_directory(), "config.ini")
        self.load_config()

    def load_config(self):
        if not os.path.exists(self.config_path):
            self.config.read_dict(self.DEFAULTS)
            self.save_config()
        else:
            self.config.read(self.config_path)

    def save_config(self):
        with open(self.config_path, 'w') as configfile:
            self.config.write(configfile)

    def get(self, section, key, fallback=None, target_type="string"):
        try:
            value = self.config[section][key]
            match target_type.lower():
                case "string":
                    return value
                case "int":
                    return int(value)
                case "float":
                    return float(value)
                case "bool":
                    return True if value == "True" else False
                case _:
                    return value

        except KeyError:
            self.logger.warning(f"Could not get section: {section} from Config using key: {key}. Using default fallback value: {fallback}")
            return fallback

    def set(self, section, key, value):
        try:
            self.config[section][key] = value
        except KeyError:
            self.logger.warning(f"Couldn't set section {section} name {key} to value {value}. Invalid section or key!")
