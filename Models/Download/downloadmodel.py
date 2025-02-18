import os

import requests

from Core.utils.utils import get_web_file_size


class DownloadModel:

    def __init__(self):
        self.url = None
        self.title = None
        self.download_file_path = None
        self.thumbnail = None
        self.downloading = False
        self.waiting_for_download = False
        self.finished_download = False
        self.paused = False
        self.file_type = None
        self.file_size = 0
        self.bytes_downloaded = 0

        self.progress_value = 0
        self.cancelled = False
        self.variables_set = False

    def set_variables(self, title, link, file_format, file_path, thumbnail):
        self.url = link
        self.title = title
        self.thumbnail = thumbnail
        self.file_type = file_format
        self.bytes_downloaded = 0
        self.download_file_path = file_path + ".fdl"
        self.file_size = get_web_file_size(link, "bytes")

        self.variables_set = True

    def receive_download_progress(self, value, bytes_downloaded):
        self.progress_value = value
        self.bytes_downloaded = bytes_downloaded
        if self.waiting_for_download:
            self.waiting_for_download = False

    def check_finish(self):
        if self.progress_value == 100:
            self.finished_download = True

    def pause_download(self):
        self.paused = True

    def cancel_download(self):
        self.cancelled = True

    def resume_download(self):
        self.paused = False

    def save_progress(self):
        ...

    def clean_files(self):
        ...

    def _rename_on_complete(self):
        new_path = self.download_file_path.split(".fdl")[0]
        os.rename(self.download_file_path, new_path)

