from kivy.uix.widget import WidgetException

from src.views.Common.common_layouts import CommonScreenManager
from src.views.baseview import BaseView


class DesktopView(BaseView):

    def __init__(self, main_view=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.main_view = main_view
        self.bind(requested_screen=self._on_screen_request)

    def add_manager(self, widget):
        if not isinstance(widget, CommonScreenManager):
            raise WidgetException(
                "Widget must be a Views.Common.common_layouts.CommonScreenManager not {}".format(type(widget)))

        self.ids.layout.add_widget(widget)

    def _on_screen_request(self, instance, screen_view):

        self.main_view.change_screen(screen_view)
