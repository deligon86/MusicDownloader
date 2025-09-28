from src.core import THEMES
from kivy.clock import Clock
from kivymd.uix.screen import MDScreen
from kivy.properties import ObjectProperty, BooleanProperty, StringProperty
from src.viewmodels.launcher_viewmodel import (
    DownloadSettingsViewModel, ThemeSettingsViewModel
)
from src.views.Common.common_widgets import ThemeButton


class WelcomeView(MDScreen):
    pass


class ThemeSettingsView(MDScreen):
    view_model: ThemeSettingsViewModel = ObjectProperty()

    def set_app_theme(self, theme):
        self.view_model.set_theme(theme)


class DownloadSettingsView(MDScreen):
    view_model: DownloadSettingsViewModel = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.view_model.bind(download_location=self.on_download_location)
        #trigger the download location
        location = self.view_model.download_location
        self.view_model.download_location = location

    def set_audio_quality(self, quality):
        """
        Set audio quality
        """
        self.view_model.set_audio_quality(quality)

    def select_download_location(self):
        Clock.schedule_once(self.view_model.set_download_location, .5)

    def set_video_quality(self, quality):
        self.view_model.set_video_quality(quality)

    def on_download_location(self, _, location):
        if location:
            self.ids.download_location.text = location


class FinishView(MDScreen):
    finished = BooleanProperty(False)

    def set_finish_flag(self):
        self.finished = True


class LauncherView(MDScreen):

    finished = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.current_page = 1
        self.add_views()

    def add_views(self):
        """
        Set up the views
        """
        self.welcome_view = WelcomeView(name="welcome")
        self.theme_view = ThemeSettingsView(view_model=ThemeSettingsViewModel(), name="theme")
        self.download_settings_view = DownloadSettingsView(view_model=DownloadSettingsViewModel(), name="d-settings")
        self.finish_view = FinishView(name="finish")
        self.finish_view.bind(finished=self.on_finish)

        self.ids.view_manager.add_widget(self.welcome_view)
        self.ids.view_manager.add_widget(self.theme_view)
        self.ids.view_manager.add_widget(self.download_settings_view)
        self.ids.view_manager.add_widget(self.finish_view)

    def finish(self):
        self.finished = True

    def next_step(self):
        self.ids.view_manager.transition.direction = "left"
        self.current_page += 1
        if self.current_page >= 4:
            self.ids.nxt.disabled = True
            self.current_page = 4

        if self.ids.prev.disabled:
            self.ids.prev.disabled = False

        if self.current_page <= 4:
            self.ids.view_manager.current = self.ids.view_manager.next()
            for child in self.ids.indic_holder.children:
                child.icon = "circle-outline"

            child = self.ids[str(self.current_page)]
            child.icon = "circle"

    def prev_step(self):
        self.ids.view_manager.transition.direction = "right"
        self.current_page -= 1
        if self.current_page <= 1:
            self.current_page = 1
            self.ids.prev.disabled = True

        if self.ids.nxt.disabled:
            self.ids.nxt.disabled = False

        if self.current_page >= 1:
            self.ids.view_manager.current = self.ids.view_manager.previous()
            for child in self.ids.indic_holder.children:
                child.icon = "circle-outline"

            child = self.ids[str(self.current_page)]
            child.icon = "circle"

    def on_finish(self, _, finished):
        self.finished = finished

