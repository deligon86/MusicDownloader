from kivymd.uix.behaviors import HoverBehavior
from kivymd.uix.floatlayout import MDFloatLayout

from Core import logger
from Views.Common.common_layouts import (
    AutoCustomThemeCard
    )
from Views.Common.common_widgets import CommonIconButton
from Models.Download.downloadmodel import DownloadModel
from kivy.properties import (
    StringProperty, BooleanProperty,
    )


class DownloadViewModelProgressContainer(HoverBehavior, MDFloatLayout):

    def __init__(self, viewmodel, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self._viewmodel = viewmodel
        self.button_container = AutoCustomThemeCard(
            CommonIconButton(
                icon="pause", on_release=self._viewmodel.pause,
                width=35, height=35, icon_size=18
                ),
            CommonIconButton(icon="close",
                             on_release=self._viewmodel.cancel_download,
                             width=35, height=35, icon_size=18
                             )
            ,
            adaptive_width=True,
            spacing=10,
            pos_hint={"right": 1, "center_y": .5},
            is_button_widget=True, height=50
            )
        self.progress = 0

    def set_progress(self, value):
        self.ids.progressbar.value = value
        self.progress = value

    def start_progress_loop(self):
        self.ids.progressbar.start()

    def stop_progress_loop(self):
        self.ids.progressbar.stop()

    def on_enter(self):
        if self.progress < 100:
            self.button_container.make_neon_effect = True
            self.add_widget(self.button_container)

    def on_leave(self):
        self.button_container.make_neon_effect = False
        self.remove_widget(self.button_container)


class DownloadViewModelButton(AutoCustomThemeCard):
    active_mode = StringProperty()
    is_button_widget = True

    def __init__(self, viewmodel, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.vm = viewmodel
        self.bind(active_mode=self._on_mode)

    def on_release(self):
        if self.active_mode == "show":
            self.vm.show_in_folder()
        elif self.active_mode == "retry":
            self.vm.retry_download()

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


class DownloadViewModel(AutoCustomThemeCard):
    icon = StringProperty()
    is_button_widget = True
    finished = BooleanProperty()

    def __init__(self, model: DownloadModel, *args, **kwargs):
        self._model = model
        super().__init__(*args, **kwargs)
        self._model.bind(
            paused=self._on_pause,
            cancelled=self._on_cancel,
            variables_set=self._on_variables,
            waiting_for_download=self._on_wait_download,
            progress_value=self._on_progress_value,
            finished_download=self._on_download_finished,
            download_failed=self._on_download_failed,
            error=self._on_error
            )
        self.show_retry_button = DownloadViewModelButton(viewmodel=self)
        self.progress_container = DownloadViewModelProgressContainer(viewmodel=self)

    def set_variables(self, title, link, file_type, file_format, download_path):
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
        self._model.set_variables(title, link, file_type, file_format, download_path)

    def pause(self, *args):
        self._model.pause_download()

    def cancel_download(self, *args):
        self._model.cancel_download()
        self.show_retry_button.active_mode = "retry"

    def resume_download(self, *args):
        self._model.resume_download()

    def retry_download(self, *args):
        self._model.retry_download()
        self.show_retry_button.disabled = True

    def show_in_folder(self, *args):
        self._model.show_file()

    def _on_cancel(self, instance, value):
        """
        If user cancelled the download stop and clean files but leave the the item on view
        User can retry to download if clicked by mistake
        :param instance:
        :param value:
        :return:
        """
        if value:
            self._model.stop_download_thread()
            self._model.clean_files()

    def _on_download_failed(self, instance, fail):
        if fail:
            self.cancel_download()
            self.finished = True
            if self._model.size_indeterminable:
                self.progress_container.stop_progress_loop()
            self.ids.progress_cont_parent.remove_widget(self.progress_container)
            self.ids.progress_cont_parent.size_hint_y = .001

    def _on_download_finished(self, instance, finished):
        if finished:
            self._model.stop_download_thread()
            self._model.rename_on_complete()
            self.show_retry_button.disabled = False
            self.finished = True
            if self._model.size_indeterminable:
                self.progress_container.stop_progress_loop()
            self.ids.progress_cont_parent.remove_widget(self.progress_container)
            self.ids.progress_cont_parent.size_hint_y = .001

    def _on_error(self, instance, error):
        # will have to post to notification channel
        logger.warning("[Download] {}".format(error))

    def _on_pause(self, instance, value):
        if value:
            # check if size is interminable and stop the progressbar loop
            if self._model.size_indeterminable:
                self.progress_container.stop_progress_loop()
        else:
            # resumed
            if self._model.size_indeterminable:
                self.progress_container.start_progress_loop()

    def _on_progress_value(self, instance, value):
        self.progress_container.set_progress(value)

    def _on_variables(self, instance, value):
        """
        When all required variables are ready for download to start
        :param instance:
        :param value:
        :return:
        """
        self._model.start_download_thread(resume=False, mode="wb")
        self.ids.progress_cont_parent.size_hint_y = .4
        self.ids.progress_cont_parent.add_widget(self.progress_container)

    def _on_wait_download(self, instance, value):
        pass
