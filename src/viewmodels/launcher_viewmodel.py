from kivy.event import EventDispatcher
from kivy.properties import (
    StringProperty
)
from tkinter import filedialog
from src.core import config, get_running_app


class DownloadSettingsViewModel(EventDispatcher):
    download_location = StringProperty(config.get("Downloads", "location"), force_dispatch=True)
    video_quality = StringProperty()
    audio_quality = StringProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def set_audio_quality(self, quality):
        self.audio_quality = quality
        config.set("Downloads", "audio_quality", quality)

    def set_download_location(self, *args):
        directory = filedialog.askdirectory(title="Select download location")
        if directory:
            self.download_location = directory
            config.set("Downloads", "location", directory)

    def set_video_quality(self, quality):
        self.video_quality = quality
        config.set("Downloads", "video_quality", quality)


class ThemeSettingsViewModel:

    @staticmethod
    def set_theme(theme):
        config.set("Theme", "theme", theme)
        get_running_app().set_theme(theme)
