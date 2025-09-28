from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen

from src.processors.download_processor import DownloadProcessor
from src.viewmodels.notification_handler_vm import NotificationHandlerViewModel


class BaseView(MDScreen):
    requested_screen = StringProperty()

    def add_manager(self, widget):
        """
        Add CommonScreenManager
        :param widget:
        :return:
        """

    def receive_screen_request(self, screen_view):
        """All buttons or widgets inside this view can request a screen change
        using this method"""
        self.requested_screen = screen_view.lower()

    def _on_screen_request(self, instance, screen_view):
        """
        Handle screen change requests it can be from internal widgets in this view
        :param instance:
        :param screen_view:
        :return:
        """


class BaseNormalScreenView(MDScreen):

    def __init__(self, main_view=None, notification_handler:NotificationHandlerViewModel=None,
                 download_processor:DownloadProcessor=None, **kwargs):
        self._main_view = main_view
        self._notification_handler = notification_handler
        self._download_processor = download_processor
        super().__init__(**kwargs)

    def on_start(self, _=None):
        """
        When the application is launching
        """

    def screen_change_command(self, name: str):
        """
        Request fired from any of the widgets in the screen that will need to
        change the screen view
        :param name:
        :return:
        """
        if self.parent:
            # will have to implement a proper way for this
            # parent is a screen manager
            self.parent.screen_view_request = name.lower()

