from kivy.properties import ObjectProperty, DictProperty
from kivymd.uix.screen import MDScreen
from kivymd.uix.responsivelayout import MDResponsiveLayout

from Views.Desktop.desktopview import DesktopView
from Views.Tablet.tabletview import TabletView
from Views.Common.common_layouts import CommonScreenManager, CommonMiniManager
from Views.Common.common_widgets import (
    CommonIconButton
)


class MainView(MDResponsiveLayout, MDScreen):

    app = ObjectProperty()
    mini_manager_parent = ObjectProperty(None)
    views = DictProperty()

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.common_screen_manager = None
        self.common_mini_manager = None
        self.bind(mini_manager_parent=self._on_mini_manager_parent)

    # expose the download api here to all views
    # title, download_url, type[Audio], file extension

    def add_to_download_queue(self, title, link, type_, format_):
        """
        :param title:
        :param link:
        :param type_:
        :param format_:
        :return:
        """

        self.views['Downloads'].add_to_queue(title, link, type_, format_)

    def on_change_screen_type(self, screen):

        # check if it's attached to a parent and detach it
        if self.common_screen_manager.parent:
            print("Removed Screen manager")
            self.common_screen_manager.parent.remove_widget(self.common_screen_manager)

        if self.app:
            self.app.screen_type = screen

    def change_screen(self, screen_name: str):
        """
        Change the screen from the main screen manager
        :param screen_name:
        :return:
        """
        self.common_screen_manager.current = screen_name.lower()
        # do other things here

    def detach_mini_manager(self):
        """
        Remove the mini manager from its current parent
        :return:
        """
        if self.common_mini_manager.parent:
            self.common_mini_manager.parent.remove_widget(self.common_mini_manager)

    def force_mini_manager(self, parent):
        """Had to use this since other parts of the code doesn't work completely
        For instance when changing mini manager parent on TabletView using side_bar_open"""
        self._on_mini_manager_parent(None, parent)

    def _on_mini_manager_parent(self, instance, parent):
        if parent:
            self.detach_mini_manager()
            parent.add_widget(self.common_mini_manager)

