from Views.baseview import BaseNormalScreenView
from kivy.properties import (
    ObjectProperty, StringProperty
)
from Views.Common.common_widgets import AccentColorButton


class SettingsView(BaseNormalScreenView):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    def add_colors(self, colors):
        for color in colors:
            self.ids.accent_cont.add_widget(
                AccentColorButton(md_bg_color=color)
            )
