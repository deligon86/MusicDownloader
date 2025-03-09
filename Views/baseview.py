from kivy.properties import StringProperty
from kivymd.uix.screen import MDScreen


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

    def __init__(self, main_view=None, *args, **kwargs):
        self._main_view = main_view
        super().__init__(*args, **kwargs)

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

