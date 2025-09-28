import os.path
from tkinter.filedialog import askdirectory
from kivy.event import EventDispatcher
from kivy.properties import StringProperty
from src.core import config


class SettingsViewModel(EventDispatcher):

    download_location = StringProperty(force_dispatch=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.common_locations = ["Music", "Documents", "Downloads", "Videos", "Pictures"]
        download_location = config.get("Downloads", "location")
        if len(os.path.split(download_location)) < 2:
            if download_location.capitalize() in self.common_locations:
                # it's a common directory e.g. Music, Documents, Downloads, Videos and Pictures
                self.download_location = os.path.join(os.path.expanduser("~"), download_location)
            else:
                # set to Downloads folder
                self.download_location = os.path.join(os.path.expanduser("~"), "Downloads")
        else:
            self.download_location = download_location

    def set_download_location(self):
        """
        Sets the download storage location
        """
        directory = askdirectory()
        if directory:
            self.download_location = directory
            config.set("Downloads", "location", str(directory))

    def set_simultaneous_downloads(self, downloads):
        config.set("Downloads", "simultaneous_downloads", str(downloads))

    def set_default_video_quality(self, quality):
        config.set("Downloads", "video_quality", quality)

    def set_default_audio_quality(self, quality):
        config.set("Downloads", "audio_quality", quality)

