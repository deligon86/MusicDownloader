from kivy.metrics import dp
from kivy.properties import StringProperty
from kivymd.uix.menu import MDDropdownMenu
from kivymd.utils import asynckivy

from Views.Common.common_layouts import AutoColumnGrid
from Views.Common.common_widgets import SongViewCardItem
from Views.baseview import BaseNormalScreenView
from ViewModels.AlbumSongs.album_viewmodel import AlbumViewModel


class SongsView(BaseNormalScreenView):

    mode = StringProperty("Songs")

    def __init__(self, view_model:AlbumViewModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_page = 1
        self._view_model = view_model
        self._view_model.bind(
            navigation_results=self._on_navigate_results,
            base_results=self._on_base_results,
        )
        self.bind(mode=self._on_mode)

        # mode menu
        mods = ["Songs", "Albums", "Foreign"]
        menu_items = [
            {
                "text": item,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=item: self.mode_menu_callback(x),
            } for item in mods
        ]
        self.mode_menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )
        self.mode_menu.position = "bottom"

    def on_start(self):
        """
        When the app starts should call this to populate the view
        :return:
        """
        self.navigate(self.ids.pager_s, "previous")

    def open_mode_menu(self, caller):
        """
        Open menu to choose mode
        :param caller:
        :return:
        """
        self.mode_menu.caller = caller
        self.mode_menu.open()

    def mode_menu_callback(self, mode):
        """
        :param mode:
        :return:
        """
        self.mode = mode
        self.mode_menu.dismiss()

    def change_view(self, view_name):
        self.ids.manager.current = view_name.lower()

    def navigate(self, pager, direction="forward"):
        """
        Navigate song pages
        :param pager: CommonLabel
        :param direction:
        :return:
        """

        if direction == "forward":
            self.current_page += 1
        else:
            if self.current_page > 1:
                self.current_page -= 1
            else:
                self.current_page = 1
        pager.text = f"Page {self.current_page}"
        self._view_model.navigate_songs(self.current_page)

    def populate_view(self, view: AutoColumnGrid, results:dict|None):
        """
        :param results:
        :param view: Grid
        :return:
        """

        async def start_widget_loading(view_, results_):
            if results_:
                view.clear_widgets()
                for title_artist, data in results.items():
                    title, artist = title_artist.split("?")
                    item = SongViewCardItem(
                        title=title, artist=artist,
                        image=data[-1], url=data[0],
                        width=view_.standard_child_width,
                        height=view_.standard_child_width + dp(20)
                    )
                    view_.add_widget(item)

        asynckivy.start(start_widget_loading(view, results))

    def _on_navigate_results(self, instance, results):
        """
        When navigation results are ready
        :param instance:
        :param results:
        :return:
        """
        match self.mode:
            case "Albums":
                self.populate_view(self.ids.albums, results)
            case "Foreign":
                self.populate_view(self.ids.foreign, results)
            case "Songs":
                self.populate_view(self.ids.songs, results)

    def _on_base_results(self, instance, results):
        """
        When base page results are ready
        :param instance:
        :param results:
        :return:
        """
        match self.mode:
            case "Albums":
                self.populate_view(self.ids.albums, results)
            case "Foreign":
                self.populate_view(self.ids.foreign, results)
            case "Songs":
                self.populate_view(self.ids.songs, results)

    def _on_mode(self, instance, value):
        """
        When mode is changed set the title and change contents in the SongsView accordingly
        :param instance:
        :param value:
        :return:
        """
        self.ids.title.text = value.capitalize()
        self._view_model.navigate_mode = value
        self.change_view(value)
