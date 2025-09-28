from kivy.clock import Clock
from kivy.properties import StringProperty, BooleanProperty, ObjectProperty
from kivy.uix.behaviors import ButtonBehavior
from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.floatlayout import MDFloatLayout

from src.viewmodels.download_viewmodel import DownloadItemViewModel
from src.views.Common.common_layouts import AutoCustomThemeCard
from src.views.Common.common_widgets import CommonLabel, CommonIconButton


class DownloadViewItemProgressContainer(HoverBehavior, MDFloatLayout):
    """
    Container that holds the progress bar
    """
    view_model = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.progress = 0
        self.button_container = None

    def add_buttons(self):
        self.button_container = AutoCustomThemeCard(
            CommonIconButton(
                icon="pause", on_release=self.view_model.pause,
                width=35, height=35, icon_size=18
                ),
            CommonIconButton(icon="close",
                             on_release=self.view_model.cancel_download,
                             width=35, height=35, icon_size=18
                             )
            ,
            adaptive_width=True,
            spacing=10,
            pos_hint={"right": 1, "center_y": .5},
            inherit_color=True, height=50
            )

    def set_progress(self, value):
        self.ids.progressbar.value = value
        self.progress = value

    def start_progress_loop(self):
        self.ids.progressbar.start()

    def stop_progress_loop(self):
        self.ids.progressbar.stop()

    def on_enter(self):
        if self.progress < 100:
            if self.button_container:
                self.button_container.make_neon_effect = True
                self.add_widget(self.button_container)

    def on_leave(self):
        if self.button_container:
            self.button_container.make_neon_effect = False
            self.remove_widget(self.button_container)


class DownloadViewItemButton(ButtonBehavior, MDBoxLayout, HoverBehavior):
    """
    A dynamic button that switches function between show in folder or retry download on download progress
    """
    active_mode = StringProperty()
    is_button_widget = True
    view_model = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.bind(active_mode=self._on_mode)

    def on_release(self):
        if self.active_mode == "show":
            self.view_model.show_in_folder()
        elif self.active_mode == "retry":
            self.view_model.retry_download()

    def on_enter(self):
        self.ids.label.make_custom = True

    def on_leave(self):
        self.ids.label.make_custom = False

    def _on_mode(self, instance, mode):
        """
        :param instance:
        :param mode:
        :return:
        """
        if mode == "show":
            self.ids.label.text = "Show in folder"
        elif mode == "retry":
            self.ids.label.text = "Retry download"


class DownloadViewItem(AutoCustomThemeCard):
    finished_download = BooleanProperty(False)
    icon = StringProperty()
    download_item_view_model: DownloadItemViewModel = ObjectProperty()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.show_retry_button = None
        self.progress_container = None
        self.view_model_binded = False

        '''if self.download_item_view_model and not self.view_model_binded:
            self.bind_download_view_model()
        else:
            self.bind(download_view_model=self.on_download_view_model)
        '''
        self.bind_download_view_model()

    def bind_download_view_model(self):
        # bind view mode
        self.view_model_binded = True
        self.show_retry_button = DownloadViewItemButton(view_model=self.download_item_view_model)
        self.progress_container = DownloadViewItemProgressContainer(view_model=self.download_item_view_model)
        self.progress_container.add_buttons()
        self.ids.btns.add_widget(self.show_retry_button)
        self.download_item_view_model.bind(
            paused=self._on_download_paused,
            cancelled=self._on_download_cancelled,
            variables_set=self._on_variables_ready,
            waiting_for_download=self._on_wait_for_download,
            download_progress=self._on_download_progress_value,
            finished_download=self._on_download_finished,
            download_failed=self._on_download_failed,
            progress_status=self._on_download_status,
            error=self._on_error
            )
        Clock.schedule_once(self.add_progress_container, 0.1)

    def add_progress_container(self, dt):
        if not self.finished_download:
            self.ids.progress_cont_parent.add_widget(self.progress_container)
            self.ids.progress_cont_parent.size_hint_y = .8

    def clear_progress_container(self):
        self.ids.progress_cont_parent.clear_widgets()
        self.ids.progress_cont_parent.size_hint_y = .001

    def get_download_path(self):
        return self.download_item_view_model.get_path()

    def set_variables(self, title, link, file_type, file_format, download_path, simulated=False, offline=False):
        """
        Set the variables before download
        :param title:
        :param link:
        :param file_type:
        :param file_format:
        :param download_path:
        :param simulated: For development testing of the behavior of the ViewModel it's components
        :param offline: Will be used when loading cached data from local storage
        :return:
        """
        thumbnail = "file"
        match file_type.lower():
            case "audio":
                thumbnail = "music-clef-treble"
            case "video":
                thumbnail = "video"
            case "zip":
                thumbnail = "zip-box"
        self.ids.icon.icon = thumbnail
        self.ids.title.text = title

        if not offline:
            self.download_item_view_model.set_variables(title, link, file_type, file_format, download_path, simulated=simulated)

    def pause_download(self, *args):
        self.download_item_view_model.pause()
        self.show_retry_button.mode = "resume"

    def cancel_download(self, *args):
        self.download_item_view_model.cancel_download()
        self.show_retry_button.active_mode = "retry"

    def resume_download(self, *args):
        self.download_item_view_model.resume_download()
        self.show_retry_button.disabled = True

    def retry_download(self, *args):
        self.download_item_view_model.retry_download()
        self.show_retry_button.disabled = True

    def show_in_folder(self, *args):
        self.download_item_view_model.show_in_folder(*args)

    def on_download_view_model(self, _, view_model):
        if view_model and not self.view_model_binded:
            self.bind_download_view_model()

    def _on_download_cancelled(self, _, cancelled):
        """
        If user cancelled the download stop and clean files but leave the the item on view
        User can retry to download if clicked by mistake
        :param _:
        :param cancelled:
        :return:
        """
        if cancelled:
            self.show_retry_button.mode = "retry"
            self.show_retry_button.disabled = False
            self.clear_progress_container()

    def _on_download_failed(self, _, fail):
        if fail:
            if self.download_item_view_model.is_size_indeterminable():
                self.progress_container.stop_progress_loop()
            self.clear_progress_container()
            self.ids.progress_cont_parent.size_hint_y = .001
            self.show_retry_button.mode = "retry"
            self.show_retry_button.disabled = False

    def _on_download_finished(self, _, finished):
        if finished:
            if self.download_item_view_model.is_size_indeterminable():
                self.progress_container.stop_progress_loop()
            #self.ids.progress_cont_parent.remove_widget(self.progress_container)
            self.clear_progress_container()
            self.show_retry_button.active_mode = "show"
            self.show_retry_button.disabled = False

            # add the link
            self.ids.progress_cont_parent.size_hint_y = .5
            self.ids.progress_cont_parent.add_widget(
                CommonLabel(
                    text=self.download_item_view_model.get_url(),
                    make_custom=True,
                    halign="left",
                    shorten=True
                )
            )

    def _on_error(self, _, error):
        """
        Post to notification
        :param _:
        :param error:
        :return:
        """
        if self.app:
            self.app.notification_handler.post_notification("Error", str(error))

    def _on_download_paused(self, _, value):
        if value:
            # check if size is interminable and stop the progressbar loop
            if self.download_item_view_model.is_size_indeterminable():
                self.progress_container.stop_progress_loop()
        else:
            # resumed
            if self.download_item_view_model.is_size_indeterminable():
                self.progress_container.start_progress_loop()

    def _on_download_progress_value(self, _, value):
        self.progress_container.set_progress(value)

    def _on_variables_ready(self, _, value):
        """
        :param _:
        :param value:
        :return:
        """
        if value:
            self.ids.progress_cont_parent.size_hint_y = .4
            self.ids.progress_cont_parent.add_widget(self.progress_container)

    def _on_download_status(self, _, status):
        if status:
            self.ids.status.text = status

    def _on_wait_for_download(self, _, wait):
        """
        :param _:
        :param wait:
        :return:
        """
        if wait:
            self.progress_container.start_progress_loop()
        else:
            self.progress_container.stop_progress_loop()

