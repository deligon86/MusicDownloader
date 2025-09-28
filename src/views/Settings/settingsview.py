from kivy.clock import Clock

from src.viewmodels.settings_viewmodel import SettingsViewModel
from src.views.baseview import BaseNormalScreenView
from kivy.properties import (
    ObjectProperty, StringProperty
)
from src.core import config, get_running_app
from src.core.utils.utils import rgb_to_hex
from src.views.Common.common_widgets import AccentColorButton, ThemeButton


class SettingsView(BaseNormalScreenView):

    def __init__(self, settings_view_model:SettingsViewModel=None, **kwargs):
        super().__init__(**kwargs)
        self.settings_view_model = settings_view_model
        self.settings_view_model.bind(download_location=self.on_download_location)
        Clock.schedule_once(self.add_menu_callbacks_configs, 1)

    def add_colors(self, colors):
        accent_color = config.get("Theme", "theme_color")
        for color in colors:
            ab = AccentColorButton(md_bg_color=color)
            self.ids.accent_cont.add_widget(ab)
            if rgb_to_hex(color) == accent_color:
                ab.trigger_action()

    def add_themes(self, themes):
        active_theme = config.get("Theme", "theme_name")
        for theme in themes:
            tb = ThemeButton(theme=theme, callback=self.update_theme)
            self.ids.theme_cont.add_widget(tb)
            tb.bind_theme_color()
            if theme == active_theme:
                tb.trigger_action()

    @staticmethod
    def update_theme(theme):
        config.set("Theme", "theme_name", str(theme))
        get_running_app().set_theme(theme)

    def add_menu_callbacks_configs(self, _):
        self.ids.sim_dl.value = config.get("Downloads", "simultaneous_downloads")
        self.ids.video_quality.value = config.get("Downloads", "video_quality")
        self.ids.audio_quality.value = config.get("Downloads", "audio_quality")
        self.ids.sim_dl.callback = self.menu_simultaneous_downloads_callback
        self.ids.video_quality.callback = self.menu_video_quality_callback
        self.ids.audio_quality.callback = self.menu_audio_quality_callback

    def menu_simultaneous_downloads_callback(self, maximum):
        """
        Set the maximum number of concurrent downloads
        """
        self.settings_view_model.set_simultaneous_downloads(maximum)

    def menu_video_quality_callback(self, quality):
        self.settings_view_model.set_default_video_quality(quality)

    def menu_audio_quality_callback(self, quality):
        self.settings_view_model.set_default_audio_quality(quality)

    def update_download_location(self, location):
        """
        :param location:
        :return:
        """
        if location != self.ids.download_loc.text:
            self.ids.download_loc.text = location

    def select_download_location(self):
        """
        :return:
        """
        self.settings_view_model.set_download_location()

    def on_download_location(self, _, location):
        if location:
            self.update_download_location(location)

