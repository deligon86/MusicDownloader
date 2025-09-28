import sys
import os
import re
import json
import logging
import requests
from PIL import Image
from src.core import config
from json import JSONDecodeError
from urllib.parse import urlparse, unquote
from src.core.base import get_app_home_directory


logger = logging.getLogger(__name__)


def strip_cdn_url(cdn_url):
    """
    Strips known CDN wrappers (e.g., WordPress i0.wp.com) and returns the original image URL.
    """
    parsed = urlparse(cdn_url)

    # Handle WordPress CDN proxy
    if parsed.netloc.endswith("wp.com") and parsed.path.startswith("/"):
        # Example: https://i0.wp.com/justnaija.com/uploads/2025/09/image.jpg
        stripped = unquote(parsed.path.lstrip("/"))
        if stripped.startswith("http://") or stripped.startswith("https://"):
            return stripped
        else:
            return f"https://{stripped}"

    # Add more CDN patterns here if needed
    return cdn_url  # Return original if no match



def format_string(word):
    """
    Replace special characters.
    Its vital for file naming
    """
    pattern = r'\W'
    new_string = re.sub(pattern, " ", word)
    return re.sub(" +", "", new_string)


def sanitize_filename(filename):
    """
    Replace problematic characters (/|\\$&) with empty spaces in a filename

    :param filename: Input filename or path
    :return: Sanitized filename with problematic characters replaced by spaces
    """
    # Define the characters to replace
    chars_to_replace = ['/', '|', '\\', '$', '&']

    # Replace each character with a space
    for char in chars_to_replace:
        filename = filename.replace(char, ' ')

    return re.sub(' +', '', filename)


def get_web_file_size(link:str="", format_:str="MB") -> int|float:
    """
    Determine the remote file size

    :param link: The target link to get size from
    :param format_: The size formating. Supported are: bytes, mb, gb

    :rtype: int|float
    :return:
        A file size value greater than 0 if the file size is determined
        0 is returned if any exception arises while getting the remote file size
    """
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
            case _:
                return size
    except:
        return 0

def is_valid_youtube_link(link):
    """
    Check if link is valid

    :param link: YouTube video link
    :rtype: bool
    :return:
        Returns True if the link is a valid YouTube video link or False is returned
    """
    pattern = r"(?:https?:\/\/)?(?:www\.)?(?:youtube\.com\/(?:embed\/|v\/|watch\?v=|watch\?feature=youtu.be\/)|(youtu\.be\/))([\w-]{11})"
    match = re.search(pattern, link)
    if match:
        return True
    else:
        return False


# select the quality from list of streams from a pytubefix.YouTube.streams
def select_stream_quality(streams, standard="128kbps", mode="audio"):
    """
    Select a stream from the specified quality from the streams

    :param streams: list of streams
    :param standard: default 126kbps in audio maximum is 326kbps, default for video 720p but depends on the stream can be upto 2k
    :param mode: audio/video
    :rtype: pytubefix.stream.Stream
    :return:
        A pytubefix.stream.Stream class
    """

    if mode == "audio":
        stream_quality = [stream.abr for stream in streams if "audio" in stream.type]
        stream_quality_int = [stream.split("kbps")[0] for stream in stream_quality]
    else:
        stream_quality = [stream.resolution for stream in streams if "video" in stream.type]
        stream_quality_int = [stream.split("p")[0] for stream in stream_quality]

    if standard in stream_quality:
        index = stream_quality.index(standard)
        return streams[index]
    else:
        indices = {}  # store the original stream index
        for i, val in enumerate(stream_quality):
            indices[val] = i

        qualities_int_sorted = sorted(stream_quality_int)
        # reconstruct the whole thing together
        if mode == "audio":
            return streams[indices[f"{qualities_int_sorted[-1]}kbps"]]
        else:
            stream = streams.filter(res=config.get("Download", "video_quality"), progressive=True).first()
            if not stream:
                # our desired quality is not in the available streams so we have to check for alternatives
                qualities = ["480p", "540p", "720p"]
                for quality in qualities:
                    stream = streams.filter(res=quality, progressive=True).first()
                    if stream:
                        break
                if not stream:
                    # Our alternative have failed so the only option is to use the highest_resolution_method
                    # although the quality is in question
                    stream = streams.get_highest_resolution()

            return stream

def is_connected(max_retry=5):
    """
    Check for internet connection

    :param max_retry: Maximum timeout in seconds
    :rtype: bool
    :return:
        True if device is connected to the internet or False
    """
    try:
        requests.get("https://google.com", timeout=max_retry)
        logger.info("Connection: Connected")
        return True
    except ConnectionError:
        logger.info("Connection: No internet")
        return False


def merge_dict(d1: dict, d2: dict):
    """
    Combine two dictionaries

    :param d1: primary dictionary
    :param d2: the dictionary to be added
    :rtype: dict
    :return:
        An updated dictionary

    """
    d1.update(d2)

    return d2


def resource_path(path=os.path.abspath("")):
    """
    Useful for handling paths in both development and production
    :param path: The resource file path
    :rtype: str
    :return:
        A valid path for both in the executable or when in development
    """
    try:
        if getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS'):
            b = sys._MEIPASS
        elif getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS:'):
            b = sys._MEIPASS
        else:
            script_path = os.path.realpath(os.path.dirname(sys.argv[0]))
            b = script_path

    except:
        b = os.path.abspath("")

    path = os.path.join(b, path)
    return path


# Update variables for classes
def set_variable(class_, variable, data, delta=None):
    """
    A function to update variables of class. First checks if the variable is valid and then updates it or logs an error
    if invalid

    :param class_: object
    :param variable: variable name
    :param data: the variable new content
    :param delta: If using kivy.clock.Clock otherwise leave to None
    :return:
    """
    valid = False
    try:
        getattr(class_, variable)
        valid = True
    except AttributeError as attr_err:
        logger.warning(f"Variable Update: Error updating variable '{variable}' in '{class_.__class__.__name__}',"
                       f"Error string {attr_err}")
    except Exception as err:
        logger.warning(f"Variable Update: Error updating variable '{variable}' in '{class_.__class__.__name__}'"
                       f"Error: {err}")

    if valid:
        setattr(class_, variable, data)


# color conversion
def rgb_to_hex(color: list | tuple):
    """
    Convert rgb/rgba color format to hex format

    :param color: A list or tuple containing the color format in kivy rgb/rgba color format e.g [.1, .2, .5] or [.1, .2, .5, 1]
    :rtype: str
    :return:
        A hex color
    """
    if len(color) == 3:
        # no alpha
        # convert from kivymd rgb to standard values
        r,g,b = [int(v * 255) for v in color]
        return f"#{r:02X}{g:02X}{b:02X}"
    else:
        # has alpha channel
        assert len(color) == 4
        r,g,b,a = [int(v * 255) for v in color]
        return f"#{a:02X}{r:02X}{g:02X}{b:02X}"


def convert_png_to_ico(image_path, save_path, sizes=None):
    try:
        image = Image.open(image_path)
        if sizes is None:
            sizes = [(256, 256), (512, 512)]

        image.save(save_path, format="ICO", sizes=sizes)
    except Exception as e:
        print("Error converting image to Ico")


def resize_image(image_path, save_path, size=None):
    try:
        image = Image.open(image_path)
        if size is None:
            size = (64, 64)

        image = image.resize(size=size, resample=Image.Resampling.LANCZOS)
        image.save(save_path, format="PNG")
    except Exception as e:
        print("Error resizing image")


# save download
def save_download_data(data:dict):
    """
    Add the item to cache
    """
    cache = list(load_download_data())
    cache.append(data)
    with open(os.path.join(get_app_home_directory(), "downloads.json"), "w") as f:
        json.dump(cache, f, indent=4)

# load downloads
def load_download_data():
    filename = "downloads.json"
    path = os.path.join(get_app_home_directory(), filename)
    if not os.path.exists(path):
        with open(path, "w") as f:
            json.dump([], f, indent=4)
    try:
        with open(path, "r") as f:
            return json.load(f)
    except JSONDecodeError:
        with open(path, "w") as f:
            json.dump([], f, indent=4)
        return []
    except Exception as e:
        return []
