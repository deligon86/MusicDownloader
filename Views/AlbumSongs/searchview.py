from kivymd.uix.menu import MDDropdownMenu
from Views.baseview import BaseNormalScreenView
from ViewModels.AlbumSongs.album_viewmodel import AlbumViewModel
from Views.Common.common_widgets import CommonSearchResult
from Core.utils.utils import get_web_file_size
from kivymd.utils import asynckivy


class SearchView(BaseNormalScreenView):

    def __init__(self, view_model: AlbumViewModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
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

    def process_item(self, title, link):
        results = self._view_model.get_downloadable_link(link)
        if results:  # [link, details, tags]
            size = get_web_file_size(results[0])
            if size >= 20:
                # possible zip file for this site
                format_ = "zip"
                type_ = "Zip"
            else:
                format_ = "mp3"  # only mp3 formats on the site
                type_ = "Audio"

            self._main_view.add_to_download_queue(title=title, link=link, type_=type_, format_=format_)

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
                widget = CommonSearchResult(
                    title=title, link=data[0],
                    image=data[1], description=data[2],
                    command=self.process_item
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
        if self.spinner.active:
            self.spinner.active = False

        print(self._view_model.error_string)
