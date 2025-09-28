from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.uix.card.card import MDCard
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.boxlayout import MDBoxLayout
from kivy.properties import (
    ObjectProperty, BooleanProperty, NumericProperty, StringProperty
)
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.recycleview import MDRecycleView
from kivy.uix.recycleboxlayout import RecycleBoxLayout
from kivymd.theming import ThemableBehavior
from kivymd.uix.widget import MDAdaptiveWidget
from kivy.core.window import Window


class AutoColumnGrid(MDGridLayout):
    """
    Common grid across mobile, tablet desktop to display tiled widgets.
    It will be the same across all devices but with different number of columns
    and children sizes:
    Mobile: ChildSize = [180, 200]
    Tablet: ChildSize = [200, 220]
    Desktop: ChildSize = [220, 240]
    """
    standard_child_width = NumericProperty(180)
    app = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_screen_type = ""
        self.prev_width = 0
        self.cols = 2
        self._event = Clock.schedule_interval(self._check_and_resize, .5)

    def _check_and_resize(self, dt):
        if self.app:
            if self.current_screen_type != self.app.screen_type:
                self.current_screen_type = self.app.screen_type
                match self.current_screen_type:
                    case "mobile":
                        self.standard_child_width = dp(180)
                    case "tablet":
                        self.standard_child_width = dp(200)
                    case "desktop":
                        self.standard_child_width = dp(220)

            if self.prev_width != self.parent.width:
                # update
                self.cols = int(self.parent.width // self.standard_child_width)
                self.prev_width = self.parent.width


class AutoCustomThemeCard(MDCard):

    app = ObjectProperty()
    """
    attribute: `app` the running application: MDApp
    """

    theme_changed = BooleanProperty(defaultvalue=False)
    """
    attribute: `theme_changed` tracks the theme and adjust colors according to the current theme
    """

    is_parent_widget = BooleanProperty(defaultvalue=False)
    """
    attribute: `is_parent_widget` for top level widgets
    """

    is_button_widget = BooleanProperty(defaultvalue=False)
    """
    attribute: `is_button_widget` for button containers
    """

    parent_type = StringProperty(defaultvalue='boxlayout')
    """
    attribute: `parent_type` one of boxlayout|gridlayout. For controlling the widget size. If gridlayout is used as a parent
            it's supposed to be AutoColumnGrid which will determine the size of this widget
    """

    inherit_color = BooleanProperty(defaultvalue=False)
    """
    attribute:  `inherit_color` use parent's background color, by default MDCard cannot do this, have to force it
    """

    make_neon_effect = BooleanProperty(defaultvalue=False)
    """
    attribute: `make_neon_effect` enable|disable the neon effect
    """

    allow_opacity = BooleanProperty(defaultvalue=False)
    """
    attribute: `allow_opacity` allow custom opacity for certain widgets which the opacity value is controlled in the
                SettingsView
    """

    allow_radius = BooleanProperty(defaultvalue=False)
    """
    attribute `allow_radius` allow use a custom radius prior to the App settings.
    """

    ripple_alpha = .4

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._size_event = Clock.schedule_interval(self._check_size, .5)
        self.bind(make_neon_effect=self._on_make_neon_effect,
                  theme_changed=self._update_theme)
        self.bind(app=self.on_app)

    def on_app(self, _, app):
            """
            it is initialized
            :param _:
            :param app:
            :return:
            """
            if app:
                app.bind(theme_name=self._set_custom_theme_style)

    def set_theme_style(self, dt):
        """
        Experiment for now. I will remove it to use the binded one
        when the app is complete
        :param dt:
        :return:
        """
        if self.app:
            self._set_custom_theme_style(self.app, self.app.theme_name)

    def _set_custom_theme_style(self, _, theme_name):
        """
        :param _:
        :param theme_name:
        :return:
        """
        # print("Theme changed")
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

    def _update_theme(self, _, update):
        """
        Trigger theme update
        :param _:
        :param update:
        :return:
        """
        if update:
            self.set_theme_style(None)

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
                    if self.parent:
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

        self.bind(screen_view_request=self._change_screen)

    def set_screen_properties(self, radius=None, elevation=0, shadow_softness=.5,
                              shadow_offset=None, shadow_softness_size=5):

        shadow_offset = [0, 0] if shadow_offset is None else shadow_offset
        for screen in self.children:
            screen.radius = radius
            screen.elevation = elevation
            screen.shadow_softness = shadow_softness
            screen.shadow_softness_size = shadow_softness_size
            screen.shadow_offset = shadow_offset

    def _change_screen(self, instance, name):
        self.current = name.lower()


class CommonRecycleView(MDRecycleView):
    pass


class CommonRecycleBoxLayout(ThemableBehavior, RecycleBoxLayout, MDAdaptiveWidget):
    pass
