import sys
import os
import re
import json
import logging
from urllib.parse import urlparse, unquote
from typing import (
    Union, Optional, List, 
    Dict, Any
)
from pathlib import Path

import requests
from PIL import Image
from json import JSONDecodeError

from src.core import config
from src.core.base import get_app_home_directory

logger = logging.getLogger(__name__)


def strip_cdn_url(cdn_url: str) -> str:
    """
    Extract original URL from CDN wrappers like WordPress i0.wp.com.
    Returns original URL if no CDN pattern matches.
    """
    parsed = urlparse(cdn_url)

    # Handle WordPress CDN
    if parsed.netloc.endswith("wp.com"):
        original_path = unquote(parsed.path.lstrip("/"))
        if original_path.startswith(("http://", "https://")):
            return original_path
        return f"https://{original_path}"

    return cdn_url


def clean_filename(text: str) -> str:
    """
    Remove problematic characters for file naming.
    Replaces special chars and multiple spaces with single characters.
    """
    # Remove special characters and normalize spaces
    cleaned = re.sub(r'\W+', '', text)
    return cleaned


def get_remote_file_size(url: str, unit: str = "MB") -> float:
    """
    Get size of remote file in specified unit.
    Returns 0.0 if request fails.
    """
    unit = unit.lower()
    size_conversions = {
        "bytes": 1,
        "kb": 1024,
        "mb": 1024 * 1024,
        "gb": 1024 * 1024 * 1024
    }

    try:
        response = requests.head(url, timeout=10)
        content_length = int(response.headers.get("Content-Length", 0))
        
        divisor = size_conversions.get(unit, 1)
        return content_length / divisor
    except Exception as e:
        logger.warning(f"Failed to get file size for {url}: {e}")
        return 0.0


def is_valid_youtube_url(url: str) -> bool:
    """
    Check if URL is a valid YouTube video link.
    Supports various YouTube URL formats.
    """
    youtube_patterns = [
        r"https?://(?:www\.)?youtube\.com/watch\?v=[\w-]{11}",
        r"https?://youtu\.be/[\w-]{11}",
        r"https?://(?:www\.)?youtube\.com/embed/[\w-]{11}",
    ]
    
    return any(re.match(pattern, url) for pattern in youtube_patterns)


def has_internet_connection(timeout: int = 5) -> bool:
    """
    Check internet connectivity by attempting to reach Google.
    Returns True if connected, False otherwise.
    """
    try:
        requests.get("https://www.google.com", timeout=timeout)
        return True
    except requests.RequestException:
        return False


def merge_dicts(primary: dict, secondary: dict) -> dict:
    """
    Merge secondary dict into primary dict.
    Returns the merged dictionary.
    """
    primary.update(secondary)
    return primary


def get_resource_path(relative_path: str = "") -> str:
    """
    Get absolute path for resources in both development and bundled environments.
    """
    if getattr(sys, 'frozen', False):
        # Running in PyInstaller bundle
        base_path = getattr(sys, '_MEIPASS', os.path.dirname(sys.executable))
    else:
        # Running in normal Python environment
        base_path = os.path.dirname(sys.argv[0])

    return os.path.join(base_path, relative_path)


def update_object_attribute(obj: object, attribute: str, value: Any) -> bool:
    """
    Safely update an object's attribute.
    Returns True if successful, False otherwise.
    """
    try:
        setattr(obj, attribute, value)
        return True
    except AttributeError as e:
        logger.warning(f"Cannot update attribute '{attribute}' in {obj.__class__.__name__} Error {e}")
        return False
    except Exception as e:
        logger.warning(f"Unexpected error updating attribute Error, {e}")
        return False


def rgb_to_hex(color: Union[List[float], tuple]) -> str:
    """
    Convert RGB/RGBA color values to hex format.
    Supports both 3-component (RGB) and 4-component (RGBA) colors.
    """
    if len(color) not in (3, 4):
        raise ValueError("Color must have 3 (RGB) or 4 (RGBA) components")

    # Convert from 0-1 range to 0-255 range
    components = [int(component * 255) for component in color]
    
    if len(components) == 3:
        r, g, b = components
        return f"#{r:02X}{g:02X}{b:02X}"
    else:
        r, g, b, a = components
        return f"#{a:02X}{r:02X}{g:02X}{b:02X}"


def convert_to_ico(png_path: str, ico_path: str, sizes: List[tuple] = None) -> bool:
    """
    Convert PNG image to ICO format.
    Returns True if successful, False otherwise.
    """
    if sizes is None:
        sizes = [(16, 16), (32, 32), (48, 48), (64, 64), (256, 256)]

    try:
        with Image.open(png_path) as img:
            img.save(ico_path, format="ICO", sizes=sizes)
        return True
    except Exception as e:
        logger.error(f"Failed to convert {png_path} to ICO: {e}")
        return False


def resize_image(image_path: str, output_path: str, size: tuple = (64, 64)) -> bool:
    """
    Resize image to specified dimensions.
    Returns True if successful, False otherwise.
    """
    try:
        with Image.open(image_path) as img:
            resized = img.resize(size, Image.Resampling.LANCZOS)
            resized.save(output_path, format="PNG")
        return True
    except Exception as e:
        logger.error(f"Failed to resize {image_path}: {e}")
        return False


def save_download_record(download_data: dict) -> None:
    """
    Save download record to persistent storage.
    Appends to existing download history.
    """
    downloads_file = Path(get_app_home_directory()) / "downloads.json"
    
    try:
        # Load existing data
        existing_data = load_download_records()
        existing_data.append(download_data)
        
        # Save updated data
        with open(downloads_file, 'w') as f:
            json.dump(existing_data, f, indent=2)
            
    except Exception as e:
        logger.error(f"Failed to save download record: {e}")


def load_download_records() -> List[dict]:
    """
    Load download history from persistent storage.
    Returns empty list if file doesn't exist or is corrupted.
    """
    downloads_file = Path(get_app_home_directory()) / "downloads.json"
    
    if not downloads_file.exists():
        # Create empty file
        downloads_file.parent.mkdir(parents=True, exist_ok=True)
        with open(downloads_file, 'w') as f:
            json.dump([], f)
        return []

    try:
        with open(downloads_file, 'r') as f:
            return json.load(f)
    except (JSONDecodeError, Exception) as e:
        logger.warning(f"Corrupted downloads file, resetting: {e}")
        # Reset corrupted file
        with open(downloads_file, 'w') as f:
            json.dump([], f)
        return []


# Backward compatibility aliases after refactor
sanitize_filename = clean_filename
is_connected = has_internet_connection
is_valid_youtube_link = is_valid_youtube_url
merge_dict = merge_dicts
set_variable = update_object_attribute
convert_png_to_ico = convert_to_ico
save_download_data = save_download_record
load_download_data = load_download_records
