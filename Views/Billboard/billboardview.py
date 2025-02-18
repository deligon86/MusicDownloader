from kivymd.uix.menu import MDDropdownMenu
from ViewModels.Billboard.billboard_viewmodel import BillBoardViewModel
from Views.baseview import BaseNormalScreenView


class BillboardView(BaseNormalScreenView):

    def __init__(self, view_model: BillBoardViewModel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._view_model = view_model

        self._view_model.bind(category=self._on_category,
                              trending_artists=self._on_artists,
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

    def _on_category(self, instance, value: str):
        """
        When category has changed
        :param instance:
        :param value:
        :return:
        """
        self.ids.title.text = value.capitalize()
        self._view_model.get_trending_songs()

    def _on_artists(self, instance, value):
        """
        :param instance:
        :param value:
        :return:
        """

    def _on_songs(self, instance, value):
        """
        :param instance:
        :param value:
        :return:
        """

    def _on_americas(self, instance, value):
        """
        :param instance:
        :param value:
        :return:
        """
