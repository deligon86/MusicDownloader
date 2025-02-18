from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.card.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import (
    ObjectProperty, BooleanProperty, NumericProperty, StringProperty
)
from kivymd.uix.screenmanager import MDScreenManager


class AutoColumnGrid(MDGridLayout):
    """
    Common grid across mobile, tablet desktop to display tiled widgets.
    It will be the same across all devices but with different number of columns
    and children sizes:
    Mobile: ChildSize = [180, 200]
    Tablet: ChildSize = [210, 230]
    Desktop: ChildSize = [230, 250]
    """
    standard_child_width = NumericProperty(180)
    app = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_screen_type = ""
        self._event = Clock.schedule_interval(self._check_and_resize, .7)

    def _check_and_resize(self, dt):
        if self.app:
            if self.current_screen_type != self.app.screen_type:
                self.current_screen_type = self.app.screen_type
                match self.current_screen_type:
                    case "mobile":
                        self.standard_child_width = dp(180)
                    case "tablet":
                        self.standard_child_width = dp(210)
                    case "desktop":
                        self.standard_child_width = dp(250)

                self.cols = self.width // self.standard_child_width


class AutoCustomThemeCard(MDCard):

    app = ObjectProperty()
    theme_changed = BooleanProperty(False)
    is_parent_widget = BooleanProperty(False)
    is_button_widget = BooleanProperty(False)
    parent_type = StringProperty('boxlayout')
    inherit_color = BooleanProperty(False)
    make_neon_effect = BooleanProperty(False)
    allow_opacity = BooleanProperty(False)
    allow_radius = BooleanProperty(False)
    ripple_alpha = .4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._event = Clock.schedule_interval(self.check_and_bind_app, .5)
        self._size_event = Clock.schedule_interval(self._check_size, .8)
        # Clock.schedule_interval(self.set_theme_style, .8)
        self.bind(make_neon_effect=self._on_make_neon_effect)

    def check_and_bind_app(self, dt):
        if self.app:
            self.app.bind(theme_name=self._set_custom_theme_style)
            Clock.unschedule(self._event)
    def set_theme_style(self, dt):
        """
        Experiment for now. I will remove it to use the binded one
        when the app is complete
        :param dt:
        :return:
        """
        if self.app:
            self._set_custom_theme_style(self.app, self.app.theme_name)

    def _set_custom_theme_style(self, app, theme_name):
        print("Theme changed")
        if not self.is_button_widget:
            match theme_name:
                case "Black":
                    if self.is_parent_widget:
                        if self.inherit_color:
                            try:
                                self.md_bg_color = self.parent.md_bg_color
                            except:
                                pass
                        else:
                            self.md_bg_color = [0, 0, 0, 1]
                    else:
                        if self.inherit_color:
                            try:
                                self.md_bg_color = self.parent.md_bg_color
                            except:
                                pass
                        else:
                            self.md_bg_color = [.02, .02, .02, 1]

                case "Dark":
                    if self.is_parent_widget:
                        if self.inherit_color:
                            try:
                                self.md_bg_color = self.parent.md_bg_color
                            except:
                                pass
                        else:
                            self.md_bg_color = [.1, .1, .1, 1]

                    else:

                        if self.inherit_color:
                            try:
                                self.md_bg_color = self.parent.md_bg_color
                            except:
                                pass
                        else:
                            self.md_bg_color = [.15, .15, .15, 1]

                case "Light":
                    if self.is_parent_widget:
                        if self.inherit_color:
                            try:
                                self.md_bg_color = self.parent.md_bg_color
                            except:
                                pass
                        else:
                            self.md_bg_color = [.86, .86, .91, 1]
                    else:

                        if self.inherit_color:
                            try:
                                self.md_bg_color = self.parent.md_bg_color
                            except:
                                pass
                        else:
                            self.md_bg_color = [.86, .86, .91, 1]
        else:
            match theme_name:
                case "Black":

                    self.md_bg_color = [.05, .05, .05, 1]

                case "Dark":
                    self.md_bg_color = [.15, .15, .15, 1]

                case "Light":
                    self.md_bg_color = [.76, .76, .8, 1]

        self.neon_effect()

    def neon_effect(self):
        if not self.app.disable_neon_effect:
            if self.make_neon_effect:
                # self.md_bg_color = self.app.active_theme_color
                self.shadow_color = self.app.theme_color
                self.shadow_softness = self.app.neon_effect_size
                self.elevation = self.app.neon_elevation
            else:
                self.shadow_color = self.md_bg_color
        else:
            self.shadow_color = self.md_bg_color

    def _on_make_neon_effect(self, instance, value):
        self.neon_effect()

    def _check_size(self, dt):
        if self.app:  # avoid early termination of the event
            if self.size_hint_x is None:
                if self.parent_type == "gridlayout":
                    if self.width != self.parent.standard_child_width:
                        self.width = self.parent.standard_child_width
                        self.height = self.width + dp(20)
            else:
                # remove the event to reduce unnecessary overheads since it has size_hint
                Clock.unschedule(self._size_event)


class CommonScreenManager(MDScreenManager):
    """
    The main screen manager across all devices
    """
    screen_view_request = StringProperty()

    def add_screens(self, screens):
        """
        Add screens from a list
        :param screens:
        :return:
        """
        for screen in screens:
            self.add_widget(screen)


class CommonMiniManager(CommonScreenManager):
    """
    Screen Manager for sidebar view which is used by tablet and desktop mode
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # I did this directly in an ugly way, the screen request is not
        # delivered to the MainView for further tweaks if any in the future
        # development. Will have to find a good way to fix this
        self.bind(screen_view_request=self._change_screen)

    def _change_screen(self, instance, name):
        self.current = name.lower()
