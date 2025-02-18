import os
import requests
from Views.Common.common_layouts import AutoCustomThemeCard
from Models.Download.downloadmodel import DownloadModel
from kivy.properties import (
    NumericProperty, StringProperty, BooleanProperty,
    ListProperty
)


class DownloadViewModel(AutoCustomThemeCard):
    pause_changed = BooleanProperty()
    cancel_changed = BooleanProperty()
    variables_updated = ListProperty()
    waiting_for_download_changed = BooleanProperty()
    progress_value_changed = NumericProperty()

    def __init__(self, model: DownloadModel, *args, **kwargs):
        self._model = model
        super().__init__(*args, **kwargs)
        self.bind(
            paused_changed=self._on_pause,
            cancel_changed=self._on_cancel,
            variables_updated_changed=self._on_variables,
            waiting_for_download_changed=self._on_wait_download,
            progress_value_changed=self._on_progress_value
        )

    def _on_pause(self, instance, value):
        pass

    def _on_cancel(self, instance, value):
        pass

    def _on_variables(self, instance, value):
        pass

    def _on_wait_download(self, instance, value):
        pass

    def _on_progress_value(self, instance, value):
        pass


    def set_variables(self, title, link, file_format, path, thumbnail):
        self._model.set_variables(title, link, file_format, path, thumbnail)
        self.variables_updated.emit(
            [
                title, link, file_format,
                path, thumbnail
            ]
        )

    def download(self, resumed=False, mode="wb"):
        downloaded = 0.000001  # avoid ZeroDivisionError
        headers = {}
        if resumed:
            headers = {'bytes-range': self._model.bytes_downloaded}
            # recalculate progress
            downloaded = self._model.bytes_downloaded

        with requests.get(self._model.url, headers=headers, stream=True) as task:
            with open(self._model.download_file_path, mode) as out_file:
                for chunk in task.iter_content(chunk_size=4096):
                    if self._model.paused:
                        break

                    if self._model.cancelled:
                        self._model.clean_files()
                        break

                    out_file.write(chunk)
                    downloaded += len(chunk)
                    try:
                        progress = int(downloaded / self._model.file_size) * 100
                    except ZeroDivisionError:
                        progress = 0
                    self.send_download_progress(progress, downloaded)


    def send_download_progress(self, value, bytes_dl):
        self._model.receive_download_progress(value, bytes_dl)
        self.progress_value_changed.emit(value)

    def pause(self):
        self._model.pause_download()
        self.pause_changed.emit(True)

    def cancel_download(self):
        self._model.cancel_download()
        self.cancel_changed.emit(True)

    def resume_download(self):
        self._model.resume_download()
        self.pause_changed.emit(False)

    def retry_download(self):
        path = os.path.split(self._model.download_file_path)
        if path[1] in os.listdir(path[0]):
            mode = "ab+"
        else:
            mode = "wb"

        self.download(resumed=True, mode=mode)
