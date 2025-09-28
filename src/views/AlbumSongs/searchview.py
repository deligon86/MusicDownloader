import re
from kivymd.uix.menu import MDDropdownMenu
from src.core import logger
from src.views.baseview import BaseNormalScreenView
from src.viewmodels.album_viewmodel import AlbumViewModel
from src.views.Common.common_widgets import CommonSearchResult
from kivymd.utils import asynckivy


class SearchView(BaseNormalScreenView):

    def __init__(self, view_model: AlbumViewModel=None, **kwargs):
        super().__init__(**kwargs)
        self.current_page = 1
        self._view_model = view_model
        self._view_model.bind(results=self._on_search_results,
                              error=self._on_error)

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

        self.spinner = self.ids.spinner

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
        self.spinner.active = True
        self._view_model.search_song(text, self.search_mode)

    def open_search_mode_menu(self, caller):
        """
        Open dropdown menu
        :param caller:
        :return:
        """
        self.control_menu.caller = caller
        self.control_menu.open()

    def process_item(self, widget: CommonSearchResult, title, link):
        self._download_processor.process_item(widget=widget, mode="hiphopkit", mini_progress=True)

    def _on_search_results(self, instance, results):
        """
        When results are ready
        :param instance:
        :param results: dict[title] = [link, image, description]
        :return:
        """
        self.spinner.active = False

        async def mini_task(items):
            for title, data in items.items():
                type_ = "songs"
                if re.search("album", title, re.I):
                    type_ = "albums"
                widget = CommonSearchResult(
                    title=title, link=data[0],
                    image=data[1], description=data[2],
                    command=self.process_item,
                    type=type_
                    )
                self.ids.content.add_widget(widget)

        asynckivy.start(mini_task(results))

    def _on_error(self, instance, error):
        """
        If error occurred
        :param instance:
        :param error:
        :return:
        """
        if error:
            if self.spinner.active:
                self.spinner.active = False

            msg = f"[SearchViewError] {error}"
            logger.warning(msg)

            self._notification_handler.post_notification(title="Error", message=msg)
