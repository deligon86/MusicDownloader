import threading

from kivy.clock import Clock
from kivy.properties import StringProperty
from kivymd.uix.menu import MDDropdownMenu
from ViewModels.Billboard.billboard_viewmodel import BillBoardViewModel
from Views.baseview import BaseNormalScreenView
from Views.Common.common_widgets import TrendingItem


class BillboardView(BaseNormalScreenView):

    def __init__(self, view_model: BillBoardViewModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view_model = view_model

        self._view_model.bind(category=self._on_category,
                              trending_songs=self._on_songs,
                              top_americas=self._on_americas)

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

    def get_top_americas(self, button):
        """
        From custom button in the view
        :return:
        """
        button.make_neon_effect = True
        self._view_model.get_top_america()

    def process_top_america_item(self, query):
        """
        Process the item before adding to download queue
        :param query:
        :return:
        """

    def process_song_item(self, query):
        """
        Process song item before enquing to download queue
        :param query:
        :return:
        """

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
                    'image': details[1]
                    }
                append(view)

            Clock.schedule_once(lambda c: self.add_to_view(view_data, c), 0)

        threading.Thread(target=mini_task, args=(songs,), daemon=True).start()

    def _on_americas(self, instance, results):
        """
        :param instance:
        :param results: dict[title] [artist]
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
                    'when_clicked': self.process_top_america_item
                    }
                append(view)

            Clock.schedule_once(lambda c: self.add_to_view(view_data, c), 0)

        threading.Thread(target=mini_task, args=(results, ), daemon=True).start()

    def add_to_view(self, view_data, dt=None):
        """
        Populate view
        :param dt:
        :param view_data: List
        :return:
        """
        self.ids.content.data = view_data
        self.ids.content.refresh_from_data()

