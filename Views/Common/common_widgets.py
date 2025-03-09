from kivy.metrics import sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.textfield.textfield import MDTextField
from kivy.properties import (
    ObjectProperty, BooleanProperty, StringProperty, DictProperty, NumericProperty, ListProperty
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
            self._on_theme_color_change(None, self.app.theme_color)
            Clock.unschedule(self._event)

    def _on_theme_color_change(self, app, color):
        self.text_color_focus = color
        self.hint_text_color_focus = color
        self.line_color_focus = color


# ###################### ###################

# ######### LABEL ##################
class CommonLabel(MDLabel):
    app = ObjectProperty()
    more_header = BooleanProperty(False)
    is_header = BooleanProperty(False)
    sub_header = BooleanProperty(False)
    small = BooleanProperty(False)
    make_custom = BooleanProperty(False)
    default_theme_text_color = StringProperty("Primary")

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
                self.text_color = self.app.theme_color
        else:
            self.theme_text_color = self.default_theme_text_color

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


class ScrollableLabel(ScrollView):
    text = StringProperty()


class CommonIcon(MDIcon):
    app = ObjectProperty()
    make_custom = BooleanProperty(False)
    default_theme_text_color = StringProperty("Primary")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._event = Clock.schedule_interval(self._check_color, 2)

    def _check_color(self, dt):
        if self.app:
            if self.make_custom:
                self.theme_text_color = "Custom"
                self.text_color = self.app.theme_color
            else:
                self.theme_text_color = self.default_theme_text_color


###################################################

# ################ IMAGES ##################
class RoundedAsyncImage(AsyncImage):
    radius = ListProperty([0, 0, 0, 0])


# ############ IconButton ##################
class CommonIconButton(AutoCustomThemeCard):
    icon = StringProperty()
    enable_custom = BooleanProperty(False)
    icon2 = StringProperty()
    icon_size = NumericProperty('20')
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


################################

# ############# YOUTUBEITEMS #################

class YouTubeItem(AutoCustomThemeCard):
    title = StringProperty()
    link = StringProperty()
    downloadable = BooleanProperty(False)

    def __init__(self, command=None, *args, **kwargs):
        self.command = command
        super().__init__(*args, **kwargs)

    def initiate_download(self):
        if self.command:
            self.command(self)


class CommonYouTubeItem(YouTubeItem):
    description = StringProperty()
    views = StringProperty()
    thumbnail = StringProperty()
    publish_date = StringProperty()
    author = StringProperty()
    duration = StringProperty()
    channel_image = StringProperty()


class CommonYouTubeHttpResultItem(YouTubeItem):
    stream_type = StringProperty()
    stream_quality = StringProperty()
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

    def __init__(self, command=None, *args, **kwargs):
        self.command = command
        super().__init__(*args, **kwargs)

    def initiate_download(self):
        if self.command:
            self.command(self.title, self.link)


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
            icon.make_custom = True
            icon.text_color = self.app.theme_color
            lbl.make_custom = True
            lbl.text_color = self.app.theme_color

    def unmark_widgets(self):
        for child in self.children:
            icon = child.children[1].children[0]
            lbl = child.children[0].children[0]
            icon.make_custom = False
            lbl.make_custom = False


############################################################


################### TrendingViewItems #######################


class TrendingItem(AutoCustomThemeCard):
    artist = StringProperty()
    image = StringProperty()

    def __init__(self, when_clicked=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.when_clicked = when_clicked


class TrendingArtistViewItem(TrendingItem):
    bio = StringProperty()
    songs = DictProperty()

    def on_release(self):
        if self.when_clicked:
            self.when_clicked(self.artist, self.bio, self.image)


class TrendingSongViewItem(TrendingItem):
    song = StringProperty()

    def on_release(self):
        self.when_clicked(f"{self.song} {self.artist}")


###########################################################


# #################### Settings Widgets #######################
class ThemeButton(MDBoxLayout):
    theme = StringProperty()
    active = BooleanProperty(False)
    app = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bind(active=self._on_active)
        self._event = Clock.schedule_interval(self._bind_theme_color, .5)

    def set_value(self, instance, value):
        self.active = value

    def _bind_theme_color(self, dt):
        if self.app:
            self.app.bind(theme_color=self._on_theme_color)
            Clock.unschedule(self._event)

    def _on_theme_color(self, instance, color):
        self.ids.check.color_active = color

    def _on_active(self, instance, value):
        if value:
            if self.app:
                self.app.set_theme(self.theme)


class AccentColorButton(ButtonBehavior, MDFloatLayout):
    app = ObjectProperty()

    def on_release(self):
        self.app.theme_color = self.md_bg_color
        self.mark_widget()

    def mark_widget(self):
        for child in self.parent.children:
            child.clear_widgets()

        self.add_widget(MDIcon(icon="check", pos_hint={"center_x": .5, "center_y": .5}))


class SwitchOptionItem(MDBoxLayout):
    option = StringProperty()
    text = StringProperty()
    active = BooleanProperty(False)
    app = ObjectProperty()

    def set_value(self, *args):
        value = args[-1]
        match self.option:
            case "font_bold":
                self.app.make_all_text_bold = value
        self.active = value


##############################################

# ############## SongView Items #############
class SongViewCardItem(AutoCustomThemeCard):
    title = StringProperty()
    artist = StringProperty()
    image = StringProperty()
    url = StringProperty()


############################################

# ############# Trending Items ######################
class TrendingSongItem(ButtonBehavior, MDBoxLayout):
    art = StringProperty()
    artist = StringProperty()
    song_name = StringProperty()
    view = ObjectProperty()

    def on_release(self):
        if self.view:
            self.view.probe_song(f"{self.song_name} {self.artist}")


class TrendingArtistItem(ButtonBehavior, MDBoxLayout):
    artist = StringProperty()
    image = StringProperty()
    view = ObjectProperty()
    number = NumericProperty()
    show_number = ObjectProperty(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(show_number=self.show_item_number)

    def show_item_number(self, instance, value):
        """
        if option is activated to show number for items
        :param instance:
        :param value:
        :return:
        """
        if value:
            self.ids.num_cont.size_hint_x = None
            lbl = CommonLabel(haligh="center", text=str(self.number))
            self.ids.num_conr.width = lbl.texture_size[0]
            self.ids.num_cont.add_widget(lbl)
        else:
            self.ids.num_cont.clear_widgets()
            self.ids.num_cont.size_hint_x = 0.001

    def on_release(self):
        if self.view:
            self.view.probe_artist(self.artist)

#######################################################
