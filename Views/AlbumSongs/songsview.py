from kivy.properties import StringProperty
from kivymd.uix.menu import MDDropdownMenu

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

    def open_mode_menu(self, caller):
        """
        Open menu to choose mode
        :param caller:
        :return:
        """

    def mode_menu_callback(self, mode):
        """
        :param mode:
        :return:
        """
        self.mode = mode
        self._view_model.navigate_mode = mode

    def navigate_songs(self, direction="forward"):
        """
        Navigate song pages
        :param direction:
        :return:
        """

        if direction == "forward":
            self.current_page += 1
        else:
            if self.current_page > 1:
                self.current_page -= 1

        self._view_model.navigate_songs(self.current_page)

    def _on_navigate_results(self, instance, results):
        """
        When navigation results are ready
        :param instance:
        :param results:
        :return:
        """
        match self.mode:
            case "Albums":
                pass
            case "Foreign":
                pass
            case "Songs":
                pass

    def _on_base_results(self, instance, results):
        """
        When base page results are ready
        :param instance:
        :param results:
        :return:
        """
        match self.mode:
            case "Albums":
                pass
            case "Foreign":
                pass
            case "Songs":
                pass

    def _on_mode(self, instance, value):
        """
        When mode is changed set the title and change contents in the SongsView accordingly
        :param instance:
        :param value:
        :return:
        """
        self.ids.title.text = self.mode
        self.ids.manager.current = self.mode.lower()
