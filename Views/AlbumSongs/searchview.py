from kivymd.uix.menu import MDDropdownMenu
from ply.yacc import call_errorfunc

from Views.baseview import BaseNormalScreenView
from ViewModels.AlbumSongs.album_viewmodel import AlbumViewModel


class SearchView(BaseNormalScreenView):

    def __init__(self, view_model: AlbumViewModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_page = 1
        self._view_model = view_model
        self._view_model.bind(results=self._on_search_results)

        self.search_mode = "All"
        # menu
        controls = ["All", "Albums", "Songs"]
        menu_items = [
            {
                "text": item,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=item: self.control_menu_callback(x),
            } for item in controls
        ]
        self.control_menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )
        self.control_menu.position = "bottom"

    def control_menu_callback(self, control):
        """
        Set control
        :param control:
        :return:
        """
        self.search_mode = control.lower()
        self.ids.mode_text.text = f"Mode: {control}"
        self.ids.mode.on_press()
        self.control_menu.dismiss()

    def search(self, text):
        self._view_model.search_song(text, self.search_mode)

    def _on_search_results(self, instance, results):
        """
        When results are ready
        :param instance:
        :param results:
        :return:
        """

    def open_search_mode_menu(self, caller):
        """
        Open dropdown menu
        :param caller:
        :return:
        """
        self.control_menu.caller = caller
        self.control_menu.open()
