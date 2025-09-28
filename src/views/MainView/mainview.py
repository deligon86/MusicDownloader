from kivy.properties import ObjectProperty, DictProperty
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.screen import MDScreen
from kivymd.uix.responsivelayout import MDResponsiveLayout
from kivymd.uix.snackbar.snackbar import MDSnackbar
from src.views.Desktop.desktopview import DesktopView
from src.views.Tablet.tabletview import TabletView
from src.views.Common.common_layouts import CommonScreenManager, CommonMiniManager
from src.views.Common.common_widgets import (
    CommonIconButton, CommonLabel
)
from src.viewmodels.notification_handler_vm import NotificationHandlerViewModel


class MainView(MDResponsiveLayout, MDScreen):

    app = ObjectProperty()
    mini_manager_parent = ObjectProperty(None)
    notification_handler = ObjectProperty(None, force_dispatch=True)
    views = DictProperty()

    def __init__(self, notification_handler:NotificationHandlerViewModel=None, **kwargs):
        super().__init__(**kwargs)
        self.common_screen_manager = None
        self.common_mini_manager = None
        self.dialog = MDDialog(type="alert")
        self.snack_label = CommonLabel()
        self.snack_view = MDSnackbar(self.snack_label)
        self.bind(mini_manager_parent=self._on_mini_manager_parent,
                  notification_handler=self.on_notification_handler)
        if notification_handler:
            self.notification_handler = notification_handler
            self.notification_handler.bind(notify=self.on_notification)

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
        For _ when changing mini manager parent on TabletView using side_bar_open"""
        self._on_mini_manager_parent(None, parent)

    def on_notification(self, _, notify, minimal=True):
        """
        Post notification. Simple for now
        :param notify
        :param minimal
        """
        if notify:
            title, message = self.notification_handler.notification_args
            if not minimal:
                self.dialog.title = title
                self.dialog.text = message
                self.dialog.open()
            else:
                self.snack_label.text = f"{title} \t {message}"
                self.snack_view.open()

    def on_notification_handler(self, _, handler):
        """
        Bind handler
        """
        if handler:
            handler.bind(notify=self.on_notification)

    def _on_mini_manager_parent(self, instance, parent):
        if parent:
            self.detach_mini_manager()
            parent.add_widget(self.common_mini_manager)

