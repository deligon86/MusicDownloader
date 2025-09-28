from kivy.clock import Clock
from kivy.event import EventDispatcher
from kivy.properties import (
    BooleanProperty, NumericProperty, ObjectProperty
)
"""
Just a basic and dirty implementation, will have to reimplement it
"""

class NotificationHandlerViewModel(EventDispatcher):
    notification_args = ObjectProperty(None, force_dispatch=True)
    notify = BooleanProperty(defaultvalue=False, force_dispatch=True)
    notification_delay = NumericProperty(0.05)  #5ms delay
    """
    Attributes:
        notification_args :  tuple of args (title, message)
        notify : Trigger notification
        notification_delay: Delay in seconds to trigger notification
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def post_notification(self, title, message):
        """
        Post notification
        Arguments:
            title (str): The notification title
            message (str) : Notification body
        """
        Clock.schedule_once(lambda c: self._do_post(title, message, c), self.notification_delay)

    def _do_post(self, title, message, _=None):
        """
        Schedule ready for post

        Arguments:
            title (str): The title of the notification
            message (str): The notification body
        """
        self.notification_args = (title, message)
        self.notify = True

