import os
import sys
from src.core import logger
from kivy.lang.builder import Builder


def resource_path(relative_path):
    """Get absolute path to resource, works for dev and PyInstaller"""
    try:
        base_path = sys._MEIPASS if hasattr(sys, '_MEIPASS') else os.path.abspath(".")
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


def load_all_kivy_files():
    kv_root = resource_path("kivy_files")
    for root, dirs, files in os.walk(kv_root):
        for file in files:
            if file.endswith(".kv"):
                full_path = os.path.join(root, file)
                Builder.load_file(full_path)
                logger.info(f"Loaded KV file: {full_path}")

