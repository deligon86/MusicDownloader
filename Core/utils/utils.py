import sys
import os
import re
import requests
from Core import logger


def get_web_file_size(link=None, format_="MB"):
    format_ = format_.lower()
    try:
        res = requests.head(link)
        size = int(res.headers["Content-Length"])
        match format_:
            case "bytes":
                return size
            case "mb":
                return size / (1024 * 1024)
            case "gb":
                return size / (1024 * 1024 * 1024)
    except:
        return 1


def is_valid_youtube_link(link):
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?feature=youtu.be\/)|(youtu\.be\/))([\w-]{11})"
    match = re.search(pattern, link)
    if match:
        return True
    else:
        return False


def is_connected(max_retry=5):
    try:
        requests.get("https://google.com", timeout=max_retry)
        logger.info("[Connection] Connected")
        return True
    except:
        logger.info("[Connection] No internet")
        return False


def merge_dict(d1: dict, d2: dict):
    d1.update(d2)

    return d2


def resource_path(path=os.path.abspath("")):
    """Useful for handling paths in both development and production"""
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            b = sys._MEIPASS
        elif getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS:'):
            b = sys._MEIPASS
        else:
            script_path = os.path.realpath(os.path.dirname(sys.argv[0]))
            # print("SCRIPT PATH: ", script_path)
            b = script_path

    except Exception:
        b = os.path.abspath("")

    path = os.path.join(b, path)
    # print("FILE PATH: ", path)
    return path


