import threading
from queue import Queue

from kivy.clock import Clock
from kivymd.uix.menu import MDDropdownMenu

from core import logger
from viewmodels.billboard_viewmodel import BillBoardViewModel
from viewmodels.youtube_viewmodel import YouTubeViewModel
from views.Common.common_layouts import AutoCustomThemeCard
from views.baseview import BaseNormalScreenView


class BillboardView(BaseNormalScreenView):

    def __init__(self, view_model: BillBoardViewModel, yt_viewmodel: YouTubeViewModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view_model = view_model
        self._yt_viewmodel = yt_viewmodel

        self._view_model.bind(category=self._on_category,
                              trending_songs=self._on_songs,
                              top_americas=self._on_americas,
                              error=self._on_error)

        # category dropdown menu
        categories = ["All", "Brazil", "France", "Italy",
                      "India", "SAfrica", "Spain", "UK"
                      ]

        category_items = [
            {
                "text": item,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=item: self.category_menu_callback(x),
            } for item in categories
        ]
        self.category_menu = MDDropdownMenu(
            items=category_items,
            width_mult=4,
        )

        self.current_stream = None
        self.lookup_patience = {}
        self.lookup_locked = False
        self.lookup_lock = threading.Lock()
        self.lookup_event = None
        self.lookup_queue = Queue()
        self.active_lookup_query = None

    def open_category_menu(self, caller):
        """
        :param caller:
        :return:
        """
        self.category_menu.caller = caller
        self.category_menu.open()

    def category_menu_callback(self, value):
        """
        :param value:
        :return:
        """
        self.category_menu.dismiss()
        self.ids.category.on_press()
        self.ids.america.make_neon_effect = False
        self._view_model.category = value.lower()

    def get_top_americas(self, button: AutoCustomThemeCard):
        """
        From custom button in billboard.kv
        :param button: invoker america | self.ids.america
        :return:
        """
        button.make_neon_effect = True
        self._view_model.get_top_america()

    def process_item(self, widget):
        """
        Process item for download
        """
        self._download_processor.process_item(widget=widget, target_media="audio")

    def _on_category(self, instance, value: str):
        """
        When category has changed
        :param instance:
        :param value:
        :return:
        """
        self.ids.title.text = value.capitalize()
        self.ids.america.make_neon_effect = False
        self._view_model.get_trending_songs()

    def _on_songs(self, instance, songs):
        """
        :param instance:
        :param songs: dict[title] [[artist, image]]
        :return:
        """

        def mini_task(data):
            view_data = []
            append = view_data.append
            for title, details in data.item():
                view = {
                    'viewclass': 'TrendingSongViewItem',
                    'song': title,
                    'artist': details[0],
                    'image': details[1],
                    'when_clicked': self.process_item
                    }
                append(view)

            Clock.schedule_once(lambda c: self.add_to_view(view_data, c), 0)

        threading.Thread(target=mini_task, args=(songs,), daemon=True).start()

    def _on_americas(self, instance, results):
        """
        :param instance:
        :param results: dict[title] [[artist,]]
        :return:
        """

        def mini_task(data):
            view_data = []
            append = view_data.append
            for title, artist in data.item():
                view = {
                    'viewclass': 'TrendingSongViewItem',
                    'title': title,
                    'artist': artist,
                    'when_clicked': self.process_item
                    }
                append(view)

            Clock.schedule_once(lambda c: self.add_to_view(view_data, c), 0)

        threading.Thread(target=mini_task, args=(results, ), daemon=True).start()

    def _on_error(self, instance, error):
        """
        When an error occurr when retrieving online content
        :param instance:
        :param error:
        :return:
        """
        if error:
            msg = f"[BillboardViewError] {error}"
            logger.warning(msg)
            self._notification_handler.post_notification(title="Error", message=msg)

    def add_to_view(self, view_data, dt=None):
        """
        Populate view
        :param dt:
        :param view_data: List
        :return:
        """
        self.ids.content.data = view_data
        self.ids.content.refresh_from_data()

