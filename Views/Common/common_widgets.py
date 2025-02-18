from kivy.metrics import sp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield.textfield import MDTextField
from kivy.properties import (
    ObjectProperty, BooleanProperty, StringProperty, DictProperty, NumericProperty
)
from Views.Common.common_layouts import AutoCustomThemeCard
from kivy.clock import Clock
from kivy.animation import Animation


# ###### TextField ######################
class CommonTextField(MDTextField):
    app = ObjectProperty(None)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._event = Clock.schedule_interval(self._bind_app_color, .4)

    def _bind_app_color(self, dt):
        if self.app:
            self.app.bind(theme_color=self._on_theme_color_change)
            Clock.unschedule(self._event)

    def _on_theme_color_change(self, app, color):
        self.text_color_focus = color
        self.hint_text_color_focus = color

# ###################### ###################

# ######### LABEL ##################
class CommonLabel(MDLabel):
    app = ObjectProperty()
    more_header = BooleanProperty(False)
    is_header = BooleanProperty(False)
    sub_header = BooleanProperty(False)
    small = BooleanProperty(False)
    make_custom = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        Clock.schedule_interval(self.configure_label, 2)

    def configure_label(self, *args):
        if self.more_header:
            self.bold = True
            if self.app:
                self.font_size = sp(self.app.more_headers_font_size)

        elif self.is_header:
            self.bold = True
            if self.app:
                self.font_size = sp(self.app.headers_font_size)

        else:
            if self.app:
                if self.sub_header:
                    self.font_size = sp(self.app.sub_header_size)
                else:
                    if self.small:
                        self.font_size = sp(self.app.small_font_size)
                    else:
                        self.font_size = sp(self.app.normal_font_size)

        if self.make_custom is True:
            if self.app:
                self.theme_text_color = "Custom"
                self.text_color = self.app.active_theme_color

        if self.app:
            if self.app.make_all_text_bold is True:
                self.bold = True
            else:
                if self.is_header:
                    pass
                elif self.more_header:
                    pass
                else:
                    self.bold = False


###################################################

# ############ IconButton ##################
class CommonIconButton(AutoCustomThemeCard):
    icon = StringProperty()
    enable_custom = BooleanProperty(False)
    icon2 = StringProperty()
    is_chevron = BooleanProperty(False)
    is_chevron_active = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event = Clock.schedule_interval(self._bind_theme_color, .5)

    def _bind_theme_color(self, dt):
        if self.app:
            self.app.bind(theme_color=self._on_theme_color)

    def _on_theme_color(self, app, color):
        if self.enable_custom:
            ttt = self.ids.icon.theme_text_color
            if ttt != "Custom":
                self.ids.icon.theme_text_color = "Custom"
                self.ids.icon.text_color = color

    def on_press(self):
        icon = self.ids.icon
        anim = Animation(font_size=sp(10), duration=.12, transition="out_bounce")
        anim.bind(on_complete=self.resize_icon)
        anim.start(icon)

        anim2 = Animation(elevation=5, duration=.12, transition="out_elastic")
        anim2.bind(on_complete=self.reset_elevation)
        anim2.start(self)

    def rotate_icon(self, icon):
        pass

    def resize_icon(self, anim, widget):
        if self.is_chevron:
            if self.is_chevron_active:
                self.is_chevron_active = False
                widget.icon = self.icon
            else:
                self.is_chevron_active = True
                widget.icon = self.icon2

        Animation(font_size=sp(26), duration=.25, transition="out_bounce").start(widget)

    @staticmethod
    def reset_elevation(anim, widget):
        Animation(elevation=0, duration=1, transition="out_elastic").start(widget)


# ###############################

############## YOUTUBEITEMS #################
class CommonYouTubeItem(AutoCustomThemeCard):
    title = StringProperty()
    link = StringProperty()
    description = StringProperty()
    views = StringProperty()
    thumbnail = StringProperty()
    publish_date = StringProperty()
    author = StringProperty()
    duration = StringProperty()
    channel_image = StringProperty()
    parent_type = "boxlayout"


class CommonYouTubeHttpResultItem(AutoCustomThemeCard):
    stream_type = StringProperty()
    stream_quality = StringProperty()
    stream_title = StringProperty()
    stream_link = StringProperty()
    stream_format = StringProperty()


#############################################

# ######## Song Search ################
class CommonSearchResult(AutoCustomThemeCard):
    title = StringProperty()
    link = StringProperty()
    description = StringProperty()
    image = StringProperty()
    artist = StringProperty()
    parent_type = "boxlayout"


# #############################

# ############# Navigation buttons #############
class NavigationButton(AutoCustomThemeCard):
    icon = StringProperty()
    text = StringProperty()


class MyNavigationBar(MDBoxLayout):
    app = ObjectProperty()
    view = ObjectProperty()

    def mark_widget(self, widget, icon, lbl):
        # do the custom command
        if self.view:
            self.view.requested_screen = lbl.text

        self.unmark_widgets()
        if self.app:
            icon.theme_text_color = "Custom"
            icon.text_color = self.app.theme_color
            lbl.theme_text_color = "Custom"
            lbl.text_color = self.app.theme_color

    def unmark_widgets(self):
        for child in self.children:
            icon = child.children[1].children[0]
            lbl = child.children[0].children[0]
            icon.theme_text_color = "Primary"
            lbl.theme_text_color = "Primary"

############################################################

################### TrendingViewItems #######################
class TrendingArtistViewItem(AutoCustomThemeCard):
    artist = StringProperty()
    bio = StringProperty()
    songs = DictProperty()
    image = StringProperty()


class TrendingSongViewItem(AutoCustomThemeCard):
    song = StringProperty()
    artist = StringProperty()
    image = StringProperty()
    url = StringProperty()


###########################################################

##################### Settings Widgets #######################
class ThemeButton(MDBoxLayout):
    theme = StringProperty()
    active = BooleanProperty(False)
    app = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bind(active=self._on_active)

    def set_value(self, *args):
        value = args[-1]
        self.active = value

    def _on_active(self, instance, value):
        if value:
            if self.app:
                self.app.theme_name = self.theme


##############################################

