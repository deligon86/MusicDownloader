from kivy.properties import BooleanProperty, StringProperty
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.screen import MDScreen
from Views.baseview import BaseView
from Views.Common.common_layouts import CommonScreenManager
from kivy.uix.widget import WidgetException


class TabletView(BaseView):

    side_bar_open = BooleanProperty(False)

    def __init__(self, main_view=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_view = main_view

        self.bind(side_bar_open=self._on_side_bar,
                  requested_screen=self._on_screen_request)

        controls = ["Side bar", "Downloads page"]
        menu_items = [
            {
                "text": item,
                "viewclass": "OneLineListItem",
                "on_release": lambda x=item: self.menu_callback(x),
            } for item in controls
        ]
        self.menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
        )

    def open_menu(self, caller):
        self.menu.caller = caller
        self.menu.open()

    def menu_callback(self, text):
        if self.main_view:
            if text == "Side bar":
                if self.side_bar_open:
                    self.side_bar_open = False
                else:
                    self.side_bar_open = True

            elif text == "Downloads page":
                self.requested_screen = "downloads"

        self.menu.dismiss()

    def add_manager(self, widget):
        if not isinstance(widget, CommonScreenManager):
            raise WidgetException("Widget must be a Views.Common.common_layouts.CommonScreenManager not {}".format(type(widget)))

        self.ids.layout.add_widget(widget)

    def _on_screen_request(self, instance, screen_view):

        self.main_view.change_screen(screen_view)

    def _on_side_bar(self, instance, open):
        if open:
            # open the side content
            self.main_view.force_mini_manager(self.ids.t_layout)
        else:
            # remove the side content
            if self.main_view:
                self.main_view.detach_mini_manager()
