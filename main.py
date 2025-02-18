import os.path
import random

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.event import EventDispatcher
from kivymd.app import MDApp
from kivy.properties import (
    StringProperty, ObjectProperty, ColorProperty
)
from loader import load_all_kivy_files
from Views.MainView.mainview import MainView
from Views.Tablet.tabletview import TabletView
from Views.Desktop.desktopview import DesktopView
from Views.Common.common_layouts import (
    CommonScreenManager, CommonMiniManager
)
from Views.DownloadViews.downloadview import DownloadView
from Views.YouTube.youtubeview import YouTubeView
from Views.AlbumSongs.songsview import SongsView
from Views.AlbumSongs.searchview import SearchView
from Views.Billboard.billboardview import BillboardView

from ViewModels.YouTube.viewmodel import YouTubeViewModel
from ViewModels.Billboard.billboard_viewmodel import BillBoardViewModel
from ViewModels.AlbumSongs.album_viewmodel import AlbumViewModel
from Models.YouTube.youtube_model import YouTubeModel
from Models.AlbumEngine.enginesmodel import HipHopKitEngineModel
from Models.Billboard.billboardmodel import BillBoardManagerModel


Window.minimum_width = 300
Window.minimum_height = 500


class MusicDownloader(MDApp):

    screen_type = StringProperty()
    theme_name = StringProperty("Dark")
    theme_color = ColorProperty([.6, .7, .8, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(screen_type=self._on_view_type_changed)
        self.main_view = None

        # set font size
        self.make_all_text_bold = False
        self.more_headers_font_size = 32
        self.headers_font_size = 26
        self.sub_header_size = 22
        self.normal_font_size = 18
        self.small_font_size = 1

        # neon effect
        self.disable_neon_effect = False
        self.neon_effect_size = 5
        self.neon_elevation = 2

    def _on_view_type_changed(self, instance, view):
        """
        For some reason, I had to do this here. If I do the clearing and reading
        widgets in the MainView.on_change_screen_type, nothing is rendered in the canvas
        :param instance: self
        :param view: ViewName
        :return:
        """
        self.main_view.clear_widgets()
        match view:
            case "mobile":
                pass
            case "tablet":
                # attach mini manager
                self.main_view.mini_manager_parent = self.tablet_view.ids.t_layout
                self.main_view.common_mini_manager.pos_hint = {"center_x": .7, "center_y": .5}
                self.main_view.add_widget(self.tablet_view)
                self.tablet_view.add_manager(self.common_screen_manager)
                print("Added screen manager")
            case "desktop":
                self.main_view.add_widget(self.desktop_view)
                self.desktop_view.add_manager(self.common_screen_manager)
                print("Added screen manager")
                # attach mini manager
                self.main_view.mini_manager_parent = self.desktop_view.ids.side_bar_layout
                self.main_view.common_mini_manager.pos_hint = {"center_x": .5, "center_y": .5}

    def set_theme(self, theme):
        self.theme_name = theme
        if theme == "Black":
            self.theme_cls.theme_style = "Dark"
        else:
            self.theme_cls.theme_style = theme

    def set_theme_color(self, color):
        self.theme_color = color

    def simulate_change_theme(self, dt):
        v = random.choice(["Light", "Dark", "Black"])
        self.set_theme(v)

    # ################### MAIN APP BUILT-INS ####################
    def on_start(self):
        """
        :return:
        """
        self.set_theme("Black")
        Clock.schedule_interval(self.simulate_change_theme, 5)

    def build(self):
        # self.load_all_kv_files(os.path.abspath("."))
        load_all_kivy_files(os.path.abspath("."))

        self.main_view = self.root
        self.tablet_view = TabletView(main_view=self.main_view)
        self.desktop_view = DesktopView(main_view=self.main_view)
        self.common_screen_manager = CommonScreenManager()

        ssv = SongsView(name="songs", view_model=AlbumViewModel(HipHopKitEngineModel()))
        sv = SearchView(name="search", view_model=AlbumViewModel(HipHopKitEngineModel()))
        ytv = YouTubeView(name="youtube", view_model=YouTubeViewModel(YouTubeModel()))
        dv = DownloadView(name="downloads")
        bv = BillboardView(name='billboard', view_model=BillBoardViewModel(BillBoardManagerModel()))
        screens = [ssv, sv, ytv, dv, bv]
        self.common_screen_manager.add_screens(screens)

        self.main_view.tablet_view = self.tablet_view
        self.main_view.desktop_view = self.desktop_view
        self.main_view.common_screen_manager = self.common_screen_manager
        self.main_view.common_mini_manager = CommonMiniManager()


    def on_stop(self):
        pass


if __name__ == '__main__':
    MusicDownloader().run()
