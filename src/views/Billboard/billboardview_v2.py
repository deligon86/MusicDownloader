import threading
import time
from collections import deque
from queue import Queue

from kivy.clock import Clock
from kivy.properties import ObjectProperty
from kivymd.uix.menu import MDDropdownMenu

from src.core import logger
from src.core.utils.utils import select_stream_quality
from src.viewmodels.billboard_viewmodel import BillBoardViewModel
from src.viewmodels.youtube_viewmodel import YouTubeViewModel
from src.views.Common.common_layouts import AutoCustomThemeCard
from src.views.baseview import BaseNormalScreenView


class BillboardView(BaseNormalScreenView):
    download_view_model = ObjectProperty()
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
        self.processing_queue = deque(maxlen=10)
        self.max_processing_timeout = 10  # seconds

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

    def process_billboard_item(self, query, dt=None):
        """
        Process the item before adding to download queue
        :param query:
        :param dt: delta
        :return:
        """

        if len(self.processing_queue) == self.processing_queue.maxlen:
            self._notification_handler.post_notification(title="Billboard item processor",
                                                         message="The processing queue is full, please wait")
            return

        if query in self.processing_queue:
            self._notification_handler.post_notification(title="Billboard item processor",
                                                         message="The item is processing, please wait")
            return
        download_item_view_model_id, _ = self.download_view_model.generate_view_model()

        threading.Thread(target=self.process_item, args=(query, download_item_view_model_id), daemon=True).start()

    def process_item(self, query, dl_view_model_id):
        """
        Process item before enqueueing to download queue
        :param query:
        :param dl_view_model_id
        :return:
        """
        with self.lookup_lock:
            lookup_timeout = self.max_processing_timeout
            while True:
                if lookup_timeout <= 0:
                    self._notification_handler.post_notification(title="Billboard item processor",
                                                                 message=f"Timeout getting query: {query}")
                    if query in self.processing_queue:
                        self.processing_queue.remove(query)
                    break

                res = self._yt_viewmodel.quick_search_url(query, audio_only=True)
                if res:
                    stream = select_stream_quality(res.streams)
                    self.download_view_model.add_to_queue(
                        title=stream.title, link=stream.url,
                        type_="Audio", format_=stream.sub_type,
                        view_model_id=dl_view_model_id
                    )
                    if query in self.processing_queue:
                        self.processing_queue.remove(query)
                    break

                lookup_timeout -= 1
                time.sleep(1)

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
        if songs:
            logger.info("[Billboard] Received top billboard songs data")
            def mini_task(data):
                view_data = []
                append = view_data.append
                for title, details in data.items():
                    view = {
                        'viewclass': 'TrendingSongViewItem',
                        'song': title,
                        'artist': details[0],
                        'image': details[1],
                        'when_clicked': self.process_billboard_item
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
        if results:
            logger.info(f"[Billboard] Received top americas data")
            def mini_task(data):
                view_data = []
                append = view_data.append
                for title, artist in data.item():
                    view = {
                        'viewclass': 'TrendingSongViewItem',
                        'title': title,
                        'artist': artist,
                        'when_clicked': self.process_billboard_item
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
            self._notification_handler.post_notification(title="Billboard Error", message=msg)

    def add_to_view(self, view_data, dt=None):
        """
        Populate view
        :param dt:
        :param view_data: List
        :return:
        """
        self.ids.content.data = view_data
        self.ids.content.refresh_from_data()

