import os
import sys
from kivy.lang.builder import Builder


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


def load_all_kivy_files(path):
    for (root, dirs, files) in os.walk(resource_path(path)):
        for file in files:
            if file.endswith(".kv"):
                full_path = resource_path(os.path.join(root, file))
                Builder.load_file(full_path)
