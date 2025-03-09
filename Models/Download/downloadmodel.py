import os

import requests
from kivy.clock import Clock

from Core.utils.customthread import CustomThread
from Core.utils.utils import get_web_file_size
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.properties import (
    StringProperty, NumericProperty,
    BooleanProperty
)


class DownloadModel(EventDispatcher):
    waiting_for_download = BooleanProperty()
    finished_download = BooleanProperty()
    paused = BooleanProperty()
    progress_value = NumericProperty()
    cancelled = BooleanProperty()
    variables_set = BooleanProperty(False)
    size_indeterminable = BooleanProperty(False)
    download_failed = BooleanProperty(False)
    error = StringProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url =None
        self.title = None
        self.download_file_path = None
        self.file_type = None
        self.file_size = None
        self.file_format = None
        self.bytes_downloaded = 0
        self.downloading = False
        self.download_thread = None

    def set_variables(self, title, link, file_type, file_format, download_location):
        """
        Set the variables necessary for download
        :param title: title of the file
        :param link: download link
        :param file_type: Audi/Video/Zip
        :param file_format: file extension
        :param download_location: download path
        :return:
        """
        self.url = link
        self.title = title
        self.file_type = file_type
        self.file_format = file_format
        self.bytes_downloaded = 0
        self.download_file_path = os.path.join(download_location, f"{title}.{file_format.lower()}.fdl")
        self.file_size = get_web_file_size(link, "bytes")
        if self.file_size == 0:
            Clock.schedule_once(lambda c: self.set_variable("size_indeterminable", True, c), 0)  # To use the progressbar loop

        Clock.schedule_once(lambda c: self.set_variable("variables_set", True, c), 0)

    def start_download_thread(self, resume=False, mode="wb"):
        self.download_thread = CustomThread(target=self.download_thread, args=(resume, mode))
        self.download_thread.daemon = True
        self.download_thread.start()

    def stop_download_thread(self):
        if self.download_thread:
            if not self.download_thread.stopped():
                self.download_thread.stop()

    def download(self, resumed=False, mode="wb"):
        downloaded = 0.000001  # avoid ZeroDivisionError if size is not determined
        headers = {}
        if resumed:
            headers = {'bytes-range': self.bytes_downloaded}
            # recalculate progress
            downloaded = self.bytes_downloaded
        try:
            with requests.get(self.url, headers=headers, stream=True) as task:
                with open(self.download_file_path, mode) as out_file:
                    for chunk in task.iter_content(chunk_size=4096):
                        if self.paused:
                            break

                        if self.cancelled:
                            self.clean_files()
                            break

                        out_file.write(chunk)
                        downloaded += len(chunk)
                        try:
                            progress_value = int(downloaded / self.file_size) * 100
                            Clock.schedule_once(lambda c: self.set_variable("progress_value", progress_value, c), 0)
                        except ZeroDivisionError:
                            Clock.schedule_once(lambda c: self.set_variable("progress_value", 0, c), 0)

            Clock.schedule_once(lambda c: self.set_variable("finished_download", True, c), 0)
        except Exception as e:
            Clock.schedule_once(lambda c: self.set_variable("download_failed", True, c), 0)
            Clock.schedule_once(lambda c: self.set_variable("error", f"Download error: {e}", c), 0)

    def pause_download(self):
        Clock.schedule_once(lambda c: self.set_variable("paused", True, c), 0)

    def cancel_download(self):
        Clock.schedule_once(lambda c: self.set_variable("cancelled", True, c), 0)

    def resume_download(self):
        Clock.schedule_once(lambda c: self.set_variable("paused", False, c), 0)

    def retry_download(self):
        path = os.path.split(self.download_file_path)
        if path[1] in os.listdir(path[0]):
            mode = "ab"
        else:
            mode = "wb"

        self.start_download_thread(resume=True, mode=mode)

    def clean_files(self):
        dir_, file_name = os.path.split(self.download_file_path)
        if file_name in os.listdir(dir_):
            if platform == "linux":
                os.system(f"rm -f {self.download_file_path}")
            elif platform == "win":
                os.system(f"del {self.download_file_path}")

    def rename_on_complete(self):
        new_path = self.download_file_path.split(".fdl")[0]
        os.rename(self.download_file_path, new_path)

    def show_file(self):
        """
        Show the file in folder
        :return:
        """
        if platform == "win":
            os.startfile(self.download_file_path)

    def set_variable(self, variable, data, dt=None):
        setattr(self, variable, data)

