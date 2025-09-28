#import os
#import pstats
import os
import sys


if getattr(sys, 'frozen', False):
    import pyi_splash


from kivy.core.window import Window
from kivy.config import Config
from kivymd.app import MDApp
from kivy.clock import Clock
from kivy.properties import (
    StringProperty, ColorProperty, ObjectProperty
)
from kivy.loader import Loader
from kivy.utils import get_color_from_hex
from src.core.utils.utils import rgb_to_hex
from src.core import logger
from processors.download_processor import DownloadProcessor

from src.loader import load_all_kivy_files, resource_path
from src.views.MainView.mainview import MainView
from src.views.Tablet.tabletview import TabletView
from src.views.Desktop.desktopview import DesktopView
from src.views.Common.common_layouts import (
    CommonScreenManager, CommonMiniManager
)
from src.views.launcher_view import LauncherView
from src.views.Artist.artist_view import ArtistView
from src.views.AlbumSongs.songsview import SongsView
from src.views.YouTube.youtubeview import YouTubeView
from src.views.AlbumSongs.searchview import SearchView
from src.views.Settings.settingsview import SettingsView
from src.views.DownloadViews.downloadview import DownloadView
from src.views.Billboard.billboardview_v2 import BillboardView
from src.views.SideBar.trendingviews import TrendingSongView, TrendingArtistView

from src.viewmodels.album_viewmodel import AlbumViewModel
from src.viewmodels.youtube_viewmodel import YouTubeViewModel
from src.viewmodels.download_viewmodel import DownloadViewModel
from src.viewmodels.settings_viewmodel import SettingsViewModel
from src.viewmodels.billboard_viewmodel import BillBoardViewModel
from src.viewmodels.notification_handler_vm import NotificationHandlerViewModel

from src.models.YouTube.youtube_model import YouTubeModel
from src.models.AlbumEngine.enginesmodel import HipHopKitEngineModel
from src.models.Billboard.billboardmodel import BillBoardManagerModel
from src.core import config, APP_NAME, get_app_home_directory


Window.minimum_width = 600
Window.minimum_height = 500


Loader.headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/134.0.0.0 Safari/537.3'}
Config.set("network", "implementation", "requests")


class MusicDownloader(MDApp):

    screen_type = StringProperty()
    theme_name = StringProperty("Light")
    theme_color = ColorProperty([.6, .7, .8, 1])
    theme_colors = [
        get_color_from_hex("#f4a1ab"),
        get_color_from_hex("#afef00"),
        get_color_from_hex("#d2fc79"),
        get_color_from_hex("#b37400"),
        get_color_from_hex("#ff00ff")
    ]
    main_view:MainView = ObjectProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = APP_NAME
        self.icon = resource_path("assets/window-icon.png")
        self.bind(screen_type=self._on_view_type_changed)
        # themes
        self.themes = ["Light", "Dark", "Black"]

        # set font size
        self.make_all_text_bold = config.get("Font", "make_all_text_bold", target_type="bold")
        self.more_headers_font_size = config.get("Font", "more_headers_font_size", target_type="int")
        self.headers_font_size = config.get("Font", "headers_font_size", target_type="int")
        self.sub_header_size = config.get("Font", "sub_header_size", target_type="int")
        self.font_size = config.get("Font", "font_size", target_type="int")
        self.small_font_size = config.get("Font", "small_font_size", target_type="int")

        # neon effect
        self.disable_neon_effect = config.get("Neon", "on", target_type="bool")
        self.neon_effect_size = config.get("Neon", "effect_size", target_type="int")
        self.neon_elevation = config.get("Neon", "elevation", target_type="int")

        self.in_first_launch = False

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
                self.main_view.common_mini_manager.size_hint_x = .4
                self.main_view.common_mini_manager.pos_hint = {"center_x": .8, "center_y": .5}
                if not self.in_first_launch:
                    self.main_view.add_widget(self.tablet_view)
                else:
                    self.main_view.add_widget(self.launcher_view)

                self.tablet_view.add_manager(self.common_screen_manager)
                # Prevent initializing the sidebar on_start in tablet mode, it has to be manually from the button
                # self.main_view.mini_manager_parent = self.tablet_view.ids.t_layout
                self.main_view.common_mini_manager.set_screen_properties(radius=[10,0,0,10], elevation=4,
                                                                         shadow_softness_size=4, shadow_softness=4,
                                                                         shadow_offset=[-12, -12])
            case "desktop":
                if not self.in_first_launch:
                    self.main_view.add_widget(self.desktop_view)
                else:
                    self.main_view.add_widget(self.launcher_view)
                self.desktop_view.add_manager(self.common_screen_manager)
                # attach mini manager
                self.main_view.common_mini_manager.size_hint_x = 1
                self.main_view.common_mini_manager.pos_hint = {"center_x": .5, "center_y": .5}
                self.main_view.mini_manager_parent = self.desktop_view.ids.side_bar_layout
                self.main_view.common_mini_manager.set_screen_properties(radius=[0]*4, elevation=2)

    def set_theme(self, theme, dt=None):
        """
        Update the app theme

        Arguments:
            theme (str): The theme name
            dt : If using kivy.clock.Clock to schedule the fuction
        """
        if theme != self.theme_name:
            self.theme_name = theme
            self.theme_cls.theme_style = "Dark" if theme == "Black" else theme
            config.set("Theme", "theme_name", theme)

    def set_theme_color(self, color):
        """
        Set the accent color of the app

        Arguments:
            color (str|list|tuple): The color to set as accent color. Can be a `hex color`, `kivy rgb/a tuple|list`
        """
        if isinstance(color, str):
            color = get_color_from_hex(color)

        self.theme_color = color
        config.set("Theme", "theme_color", rgb_to_hex(color))

    # ################### MAIN APP BUILT-INS ####################
    def on_start(self):
        """
        :return:
        """
        if getattr(sys, 'frozen', False):
            pyi_splash.close()

        if "first_launch.rd" in os.listdir(get_app_home_directory()):
            settings = self.main_view.views.get("Settings")
            settings.add_colors(self.theme_colors)
            settings.add_themes(self.themes)
            settings.update_download_location(config.get("Downloads", "location", "Downloads"))
            self.main_view.tablet_view = self.tablet_view
            self.main_view.desktop_view = self.desktop_view
            Clock.schedule_once(self.start_activities, 3)
        else:
            self.start_launcher()

    def on_launcher_finished(self, _, finished):
        if finished:
            settings = self.main_view.views.get("Settings")
            settings.add_colors(self.theme_colors)
            settings.add_themes(self.themes)
            settings.update_download_location(config.get("Downloads", "location", "Downloads"))
            self.common_screen_manager.current = "songs"
            Clock.schedule_once(self.start_activities, 3)

            self.main_view.desktop_view = self.desktop_view
            self.main_view.tablet_view = self.tablet_view
            self.in_first_launch = False
            Window.minimum_width = 600
            Window.minimum_height = 500
            view_type = self.main_view.get_real_device_type()
            if view_type == "tablet":
                self.main_view.add_widget(self.tablet_view)
            elif view_type == "desktop":
                self.main_view.add_widget(self.desktop_view)

            with open(os.path.join(get_app_home_directory(), "first_launch.rd"), "w") as f:
                f.write("True")

    def start_activities(self, dt):
        """
        Start loading heavy activities after start up
        :return:
        """
        self.main_view.views.get("Downloads").on_start()
        self.main_view.views.get("Songs").on_start()

    def start_launcher(self):
        """
        When the app has been launched for the first time
        """
        self.main_view.tablet_view = self.launcher_view
        self.main_view.desktop_view = self.launcher_view

    def build(self):
        load_all_kivy_files()
        self.main_view = self.root
        if "first_launch.rd" not in os.listdir(get_app_home_directory()):
            self.in_first_launch = True
            Window.minimum_width = 800
            Window.minimum_height = 600

        self.launcher_view = LauncherView(name="launcher")
        self.launcher_view.bind(finished=self.on_launcher_finished)

        self.notification_handler = NotificationHandlerViewModel()
        self.download_view_model = DownloadViewModel(notification_handler=self.notification_handler)
        self.youtube_model = YouTubeModel()
        self.download_processor = DownloadProcessor(notification_handler=self.notification_handler,
                                                    youtube_view_model=YouTubeViewModel(YouTubeModel()),
                                                    album_view_model=AlbumViewModel(HipHopKitEngineModel()),
                                                    download_view_model=self.download_view_model)


        self.main_view.notification_handler = self.notification_handler
        self.tablet_view = TabletView(main_view=self.main_view)
        self.desktop_view = DesktopView(main_view=self.main_view)
        self.common_screen_manager = CommonScreenManager()

        ssv = SongsView(name="songs", main_view=self.main_view, view_model=AlbumViewModel(HipHopKitEngineModel()),
                        download_processor=self.download_processor, notification_handler=self.notification_handler)

        sv = SearchView(name="search", main_view=self.main_view, view_model=AlbumViewModel(HipHopKitEngineModel()),
                        download_processor=self.download_processor, notification_handler=self.notification_handler)

        ytv = YouTubeView(name="youtube", main_view=self.main_view, view_model=YouTubeViewModel(self.youtube_model),
                          download_processor=self.download_processor, notification_handler=self.notification_handler)
        dv = DownloadView(name="downloads", main_view=self.main_view, download_view_model=self.download_view_model)
        bv = BillboardView(name='billboard', main_view=self.main_view,
                           view_model=BillBoardViewModel(BillBoardManagerModel()),
                           yt_viewmodel=YouTubeViewModel(self.youtube_model),
                           download_view_model=self.download_view_model,
                           download_processor=self.download_processor, notification_handler=self.notification_handler)

        stv = SettingsView(name="settings", notification_handler=self.notification_handler,
                           settings_view_model=SettingsViewModel())
        trs = TrendingSongView(name="tr-song", main_view=self.main_view,
                               view_model=BillBoardViewModel(BillBoardManagerModel()),
                               yt_vm=YouTubeViewModel(self.youtube_model),
                               download_processor=self.download_processor,
                               notification_handler=self.notification_handler)
        tra = TrendingArtistView(name="tr-artist", main_view=self.main_view,
                                 billboard_vm=BillBoardViewModel(BillBoardManagerModel()),
                                 album_dl_vm=AlbumViewModel(HipHopKitEngineModel()),
                                 notification_handler=self.notification_handler
                                 )
        av = ArtistView(name="artist view", album_vm=AlbumViewModel(HipHopKitEngineModel()),
                        download_processor=self.download_processor, notification_handler=self.notification_handler)

        screens = [ssv, sv, ytv, dv, bv, stv, av]
        views = {
            "Songs": ssv, "Search": sv, "YouTube": ytv,
            "Downloads": dv, "Billboard": bv, "Settings": stv,
            "Trs": trs, "Tra": tra, "Artist View": av
        }

        self.main_view.views = views
        self.common_screen_manager.add_screens(screens)
        self.main_view.common_screen_manager = self.common_screen_manager
        self.main_view.common_mini_manager = CommonMiniManager()
        self.main_view.common_mini_manager.add_screens([tra, trs])

    def on_stop(self):
        config.save_config()


if __name__ == '__main__':
    app = MusicDownloader()
    app.run()

