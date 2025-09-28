from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty
from kivymd.uix.boxlayout import MDBoxLayout
from src.viewmodels.download_viewmodel import DownloadItemViewModel


class DownloadViewItemMini(MDBoxLayout):
    view_model:DownloadItemViewModel = ObjectProperty()
    status = StringProperty()
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.paused = False
        self.bind(status=self._on_status, view_model=self._on_view_model)

    def add_control_buttons(self):
        self.ids.progress_cont.add_buttons()

    def pause(self):
        """
        :return:
        """
        if self.paused:
            if self.view_model:
                self.view_model.resume_download()
                self.paused = False
        else:
            if self.view_model:
                self.view_model.pause()
                self.paused = True

    def cancel(self):
        """
        :return:
        """
        if self.view_model:
            self.view_model.cancel_download()
        else:
            # clean widgets and processes
            pass

    def _on_view_model(self, _, view_model):
        """
        :param _:
        :param view_model:
        :return:
        """
        if view_model:
            view_model.bind(paused=self._on_pause,
                            finished_download=self._on_download_finished,
                            cancelled=self._on_cancel_download,
                            waiting_for_download=self._on_wait_for_download,
                            download_progress=self._on_progress,
                            progress_status=self._on_status)
            self.view_model.wait_for_download = True
            self.ids.progress_cont.view_model = view_model

        print("MiniItem view model Init: ", view_model)

    def _on_pause(self, _, paused):
        """
        :param _:
        :param paused:
        :return:
        """
        if paused:
            self.status = "Paused"
        else:
            self.status = "Resuming.."

    def _on_progress(self, _, progress):

        self.ids.progress_cont.set_progress(progress)

    def _on_status(self, _, message):
        """
        :param _:
        :param message:
        :return:
        """
        def set_status(_):
            self.ids.info.text = message

        Clock.schedule_once(set_status)

    def _on_download_finished(self, _, finish):
        """
        :param _:
        :param finish:
        :return:
        """
        if finish:
            self.ids.progress_cont.set_progress(100)
            self.status = "Done"
            self.parent.height = 0
            self.parent.remove_widget(self)

    def _on_cancel_download(self, _, cancel):
        """
        :param _:
        :param cancel:
        :return:
        """
        if cancel:
            self.status = 'Cancelled'

    def _on_wait_for_download(self, _, wait):
        """
        :param _:
        :param wait:
        :return:
        """
        # it can be used in a thread so schedule in main thread
        def wait_download(_):
            if wait:
                self.ids.progress_cont.start_progress_loop()
            else:
                self.ids.progress_cont.stop_progress_loop()

        Clock.schedule_once(wait_download, 0.002)

