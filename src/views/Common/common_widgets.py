from kivy.metrics import sp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.image import AsyncImage
from kivy.uix.scrollview import ScrollView
from kivymd.uix.behaviors.focus_behavior import FocusBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.label import MDLabel, MDIcon
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.textfield.textfield import MDTextField
from kivy.properties import (
    ObjectProperty, BooleanProperty, StringProperty, DictProperty, NumericProperty, ListProperty
    )
from src.views.Common.common_layouts import AutoCustomThemeCard
from kivy.clock import Clock
from kivy.animation import Animation
from src.views.DownloadViews.downloadviewitemmini import DownloadViewItemMini
from src.core import logger, get_running_app


# ###### TextField ######################
class CommonTextField(MDTextField):

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._event = Clock.schedule_interval(self._bind_app_color, .4)

    def _bind_app_color(self, dt):
        """
        Bind the color
        :param dt: Delta for clock
        """
        app = get_running_app()
        if app:
            app.bind(theme_color=self._on_theme_color_change)
            self._on_theme_color_change(None, app.theme_color)
            Clock.unschedule(self._event)

    def _on_theme_color_change(self, app, color):
        """
        When theme color has changed
        :param app: Application
        :param color: Theme color
        """
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
        Clock.schedule_interval(self.configure_label, 1)

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
                        self.font_size = sp(self.app.font_size)

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

        Animation(font_size=sp(self.icon_size), duration=.25, transition="out_bounce").start(widget)

    @staticmethod
    def reset_elevation(anim, widget):
        Animation(elevation=0, duration=1, transition="out_elastic").start(widget)


##############################################


# ############# YOUTUBEITEMS #################

class BaseQueryItem(AutoCustomThemeCard):
    status = StringProperty()
    link = StringProperty()
    title = StringProperty()
    progress_cont = ObjectProperty()
    downloadable = BooleanProperty(False)
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(status=self.on_status)

    def add_progress_container(self):
        """
        :return:
        """

    def on_status(self, _, message):
        """
        Update the status
        """


class YouTubeItem(BaseQueryItem):

    def __init__(self, command=None, **kwargs):
        self.command = command
        super().__init__(**kwargs)

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

    def add_progress_container(self):
        """
        :return:
        """
        self.progress_cont = DownloadViewItemMini()
        self.ids.prog_cont.add_widget(self.progress_cont)
        self.ids.prog_cont.height = 35


    def on_status(self, _, message):
        """
        :param _:
        :param message:
        :return:
        """


class CommonYouTubeHttpResultItem(YouTubeItem):
    stream_type = StringProperty()
    stream_quality = StringProperty()
    stream_format = StringProperty()

    def add_progress_container(self):
        """
        :return:
        """
        self.progress_cont = DownloadViewItemMini()
        self.ids.prog_cont.add_widget(self.progress_cont)
        self.ids.prog_cont.height = 35

    def on_status(self, _, message):
        pass


#############################################


# ######## Song Search ################
class CommonSearchResult(BaseQueryItem):
    description = StringProperty()
    image = StringProperty()
    artist = StringProperty()
    type = StringProperty()
    parent_type = "boxlayout"

    def __init__(self, command=None, *args, **kwargs):
        self.command = command
        super().__init__(*args, **kwargs)

    def add_progress_container(self):
        """
        :return:
        """
        self.progress_cont = DownloadViewItemMini()
        self.ids.prog_cont.add_widget(self.progress_cont)
        self.ids.prog_cont.height = 35

    def initiate_download(self):
        if self.command:
            self.command(self, self.title, self.link)

    def on_status(self, _, message):
        pass


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


class TrendingItem(BaseQueryItem):
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
        if self.when_clicked:
            self.when_clicked(f"{self.song} {self.artist}")


###########################################################


# #################### Settings Widgets #######################
class ThemeButton(MDBoxLayout):
    theme = StringProperty()
    active = BooleanProperty(False)
    callback = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.bind(active=self._on_active)

    def bind_theme_color(self):
        get_running_app().bind(theme_color=self._on_theme_color)

    def set_value(self, instance, value):
        self.active = value

    def trigger_action(self):
        """
        Trigger checkbox press
        """
        self.ids.check.trigger_action()

    def _on_theme_color(self, instance, color):
        self.ids.check.color_active = color

    def _on_active(self, instance, value):
        if value:
            if self.ids.check.active != value:
                self.ids.check.active = value

            if not self.callback:
                get_running_app().set_theme(self.theme)
            else:
                # using a custom callback rather than setting the theme directly
                self.callback(self.theme)


class AccentColorButton(ButtonBehavior, MDFloatLayout):
    app = ObjectProperty()

    def on_release(self):
        self.app.set_theme_color(self.md_bg_color)
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


class FontSizeBox(MDFloatLayout, FocusBehavior):
    app = ObjectProperty()
    value_error = BooleanProperty(False)

    def receive_font_size(self, size):
        """
        Get size when Enter key is pressed in the font box
        :param size:
        :return:
        """
        try:
            font_size = int(size)
            if self.app:
                # set font directly
                if 13 <= font_size <= 24:
                    self.app.font_size = font_size
                    if self.value_error:
                        self.value_error = False
                else:
                    raise ValueError("Font is larger")
        except:
            self.ids.line.md_bg_color = "red"
            self.value_error = True

    def adjust_focus(self, textfield, focus):
        """
        :param textfield:
        :param focus:
        :return:
        """
        if focus:
            color = self.app.theme_color if not self.value_error else [1, 0, 0, 1]
            Animation(md_bg_color=color, width=self.width, height=2, duration=.3).start(self.ids.line)
        else:
            if not self.value_error:
                def revert_line(anim, widget):
                    Animation(width=self.width, height=3, duration=.2).start(self.ids.line)
                a = Animation(md_bg_color=[.5, .5, .5, .5], width=0, height=0, duration=.2)
                a.bind(on_complete=revert_line)
                a.start(self.ids.line)


#############################################


# ############## SongView Items #############
class SongViewCardItem(TrendingItem):
    """
    Card to display the Songs|Albums|Foreign
    """
    title = StringProperty()
    artist = StringProperty()
    image = StringProperty()
    url = StringProperty()
    link = StringProperty()
    type = StringProperty(defaultvalue="songs")
    parent_type = "gridlayout"
    """
    attribute: type can be any of: songs, albums, foreign
    """
    default_width = NumericProperty()

    def add_progress_container(self):
        """
        :return:
        """
        self.progress_cont = DownloadViewItemMini()
        self.ids.prog_cont.add_widget(self.progress_cont)
        self.ids.prog_cont.height = 35

    def on_release(self):
        if self.when_clicked:
            self.when_clicked(self, self.title, self.artist, self.url)

    def on_enter(self):
        """
        Enable neon effect
        :return:
        """
        self.make_neon_effect = True

    def on_leave(self):
        """
        Disable neon effect
        :return:
        """
        self.make_neon_effect = False

    def on_status(self, _, message):
        """
        :param _:
        :param message:
        :return:
        """
        if 'prog_cont' in self.ids:
            self.ids.prog_cont.status = message


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
    show_number = BooleanProperty(False)

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


############## Menu Item ##############################
class MenuDropDown(AutoCustomThemeCard):
    type_ = StringProperty()
    value = StringProperty()
    values = ListProperty()  # strings
    icon_size = NumericProperty("25sp")
    icon_wh = ListProperty([30, 30])
    callback = None
    has_menu_items = BooleanProperty(False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(value=self.on_value)
        self.menu = MDDropdownMenu()
        if self.values:
            self.menu.items = self.create_menu_items()
            self.has_menu_items = True
        else:
            logger.warning("Menu dropdown: Dropdown Menu for type {} has no values. Cannot create menu".format(self.type_))

        # first item to be Select
        self.values.append("Select")

    def on_release(self):
        """
        :return:
        """
        if self.menu.items:
            self.open_menu(self.ids.caller)
        else:
            self.create_menu(self.ids.caller)

    def on_value(self, *args):
        self.ids.lbl.text = self.value

    def create_menu(self, caller):
        if not self.menu.items:
            self.menu.items = self.create_menu_items()
            self.has_menu_items = True

        self.open_menu(caller)

    def create_menu_items(self):
        menu_items = [
            {
                'text': str(text),
                'viewclass': "OneLineListItem",
                'on_release': lambda x=text: self.menu_pressed(x)
                }
            for text in self.values
            ]
        return menu_items

    def open_menu(self, caller):
        self.menu.caller = caller
        self.menu.open()

    def update_values(self, value):
        """
        :param value:
        :return:
        """
        # convert to string
        value = str(value)
        self.value = value
        self.ids.lbl.text = value
        logger.info("Menu dropdown: type {}, value {}".format(self.type_, self.value))

    def menu_pressed(self, value):
        """
        On menu activate
        :param value (str): The callback item
        """
        self.update_values(value)
        if self.callback:
            self.callback(value)
        else:
            logger.warning("Menu dropdown: No Callback given for Dropdown type {}".format(self.type_))

        self.menu.dismiss()

###################################################################
