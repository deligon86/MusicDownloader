import datetime
import os
import queue
import random
import string
from src.core import (
    logger, config
)
from src.core.utils.utils import save_download_data, load_download_data
from kivy.clock import Clock
from kivy.event import EventDispatcher
from src.models.Download.downloadmodel import DownloadModel
from kivy.properties import (
    StringProperty, BooleanProperty,
    NumericProperty, ObjectProperty, ListProperty,
)
from src.viewmodels.notification_handler_vm import NotificationHandlerViewModel
from .batch_loader import BatchLoader


class DownloadItemViewModel(EventDispatcher):
    waiting_for_download = BooleanProperty(defaultvalue=False, force_dispatch=True)
    finished_download = BooleanProperty(defaultvalue=False, force_dispatch=True)
    paused = BooleanProperty(defaultvalue=False)
    download_progress = NumericProperty(defaultvalue=0, force_dispatch=True)
    cancelled = BooleanProperty(defaultvalue=False)
    variables_set = BooleanProperty(False)
    size_indeterminable = BooleanProperty(False)
    download_failed = BooleanProperty(False, force_dispatch=True)
    error = StringProperty()
    progress_status = StringProperty("", force_dispatch=True)
    download_id = StringProperty()

    def __init__(self, model:DownloadModel=None, **kwargs):
        self._model = model
        super().__init__(**kwargs)
        self._model.bind(
            paused=self._on_pause,
            cancelled=self._on_cancel,
            variables_set=self._on_variables,
            waiting_for_download=self._on_wait_download,
            progress_value=self._on_progress_value,
            finished_download=self._on_download_finished,
            download_failed=self._on_download_failed,
            error=self._on_error,
            status=self._on_download_status
            )

    @property
    def model(self):
        return self._model

    def get_url(self):
        """
        Get the download url

        :rtype: str
        Returns:
            A download url
        """
        return str(self._model.url)

    def get_title(self):
        return self._model.title

    def get_filetype(self):
        return self._model.file_type

    def get_path(self):
        """
        Get the target file path

        :rtype: str
        Returns:
            The target file path
        """
        return self._model.download_file_path

    def is_size_indeterminable(self):
        """
        Check if size is valid

        :rtype: str
        Returns:
            True if the size is determinable or False
        """
        return self._model.size_indeterminable

    def set_variables(self, title, link, file_type, file_format, download_path, simulated=False):
        """
        Set the variables before download

        Arguments:
            title (str): The item title
            link (str): The download link
            file_type (str): `Audio`, `Video`, `Zip`
            file_format (str): The file extension
            download_path (str):
            simulated (bool): For development testing of the behavior of the ViewModel and associated view components

        Returns:
        """
        self._model.wait_for_download = True
        self._model.set_variables(title, link, file_type, file_format, download_path, simulated=simulated)

    def pause(self, *args):
        """
        Pause download
        """
        self._model.pause_download()

    def cancel_download(self, *args):
        """
        Cancel the download
        """
        self._model.cancel_download()

    def resume_download(self, *args):
        """
        Resume the download
        """
        self._model.resume_download()

    def retry_download(self, *args):
        """
        Retry the download
        """
        self._model.retry_download()

    def show_in_folder(self, *args):
        """
        Navigate to the download folder
        """
        self._model.show_file()

    def _on_cancel(self, _, value):
        """
        If user cancelled the download stop and clean files but leave the item on view
        User can retry to download if clicked by mistake

        Arguments:
            _: Model instance
            value (bool): if cancelled

        """
        if value:
            self._model.stop_download_thread()
            self._model.clean_files()
            self.cancelled = True

    def _on_download_failed(self, instance, fail):
        """
        The download has failed

        Arguments:
            instance: model
            fail (bool):
        """
        if fail:
            self.cancel_download()
            self.download_failed = True

    def _on_download_finished(self, _, finished):
        """
        Download has finished

        Arguments:
            _: model
            finished (bool):
        """
        if finished:
            self._model.stop_download_thread()
            self.finished_download = True

    def _on_download_status(self, _, status):
        """
        Download progress status e.g `1.2MB/26.5MB

        Arguments:
            _: model
            status (str): progress status
        """
        if status:
            self.progress_status = status

    def _on_error(self, _, error):
        """
        An error has occurred during download
        """
        self.error = error

    def _on_pause(self, _, value):
        """
        Download has been paused
        """
        self.paused = value

    def _on_progress_value(self, _, value):
        """
        Download progress value is recieved
        """
        self.download_progress = value

    def _on_variables(self, _, value):
        """
        When all required variables are ready for download to start
        :param _:
        :param value:
        :return:
        """
        if value:
            self._model.start_download_thread(resume=False, mode="wb")
            logger.info("[DownloadManager] Download started")

    def _on_wait_download(self, _, value):
        self.waiting_for_download = value


class DownloadViewModel(EventDispatcher):
    download_task = ObjectProperty({}, force_dispatch=True)
    download_cache_batch = ListProperty([], force_dispatch=True)
    simulate_downloads = BooleanProperty(False)
    silent_notification = BooleanProperty(True)
    """
    Attributes:
        download_task: dict of download arguments
        simulate_downloads: To be used in testing widgets behavior
    """
    def __init__(self, notification_handler:NotificationHandlerViewModel=None, **kwargs):
        super().__init__(**kwargs)
        self._notification_handler = notification_handler
        self.download_queue = queue.Queue()
        self.active_task_count = 0
        self.maximum_task_count = config.get("Downloads", "simultaneous_downloads", 3, "int")
        self._active_item_view_models = {}

        self.common_locations = ["Music", "Documents", "Downloads", "Videos", "Pictures"]
        download_location = config.get("Downloads", "location", "Downloads")
        self.download_location = self.valid_download_path(download_location)
        os.makedirs(self.download_location, exist_ok=True)

        # batch loader
        self.batch_loader = BatchLoader(data_source=load_download_data(), on_batch=self.dispatch_download_cache_batch,
                                        on_complete=self.batch_complete, batch_size=5
                                        )

    def start_batch_loader(self):
        self.batch_loader.start()

    def dispatch_download_cache_batch(self, batch):
        self.download_cache_batch = batch

    def batch_complete(self):
        # enable notifications
        self.silent_notification = False

    def valid_download_path(self, location):
        """
        Determine the storage location path
        """
        if os.path.exists(location):
            return location
        else:
            if location in self.common_locations:
                return os.path.join(os.path.expanduser("~"), location)
            else:
                # Simple for now, but will have to resolve the path in an efficient way
                return location

    def add_to_queue(self, title, link, type_, format_, view_model_id):
        """
        Add task to download queue

        Arguments:
            title (str):
            link (str):
            type_ (str): File type. `Audio`, `Video`, `Zip`
            format_ (str): File extension. `.mp3`, `.mp4`, `.zip`, `.webm`, e.t.c
            view_model_id (str): Generated ViewModel id
        """
        if not view_model_id:
            # generate a new view model for this item
            raise ValueError(f"view_model_id must not be None. Generate a view model first before initializing")

        task = {
            "title": title,
            "link": link,
            "type": type_,
            "format": format_,
            "view_model_id": view_model_id
        }
        if self.active_task_count > self.maximum_task_count:
            self.download_queue.put(task)
            logger.info(f"[Download] Added to queue `{title}`")
        else:
            # ensure its set in a main thread
            Clock.schedule_once(lambda c: self.set_task(task, c), 0.01)
            self.active_task_count += 1

    def set_task(self, task, _):
        """
        Set the task

        Arguments:
            task (dict): The download task
            _: Delta variable for use in kivy.clock.Clock.schedule_once meth

        """
        self.download_task = task

    def get_item_view_model(self, view_model_id):
        """
        Get an DownloadItemViewModel by its ID

        Arguments:
            view_model_id (str): The id for the view model

        Returns:
            The queried view model `viewmodels.download_viewmodel.DownloadItemViewModel`
        """
        return self._active_item_view_models.get(view_model_id)

    def remove_item_view_model(self, view_model_id):
        """
        Removes the view model from the active task list

        Arguments:
            view_model_id (str): View model id to remove

        """
        try:
            vm = self._active_item_view_models.pop(view_model_id)
            logger.info(f"[DownloadViewModel] Removed {view_model_id}->{vm}")
        except Exception as e:
            logger.warning(f"[DownloadViewModel] Couldn't remove view_model_id {view_model_id} error '{e}'")

    def generate_view_model(self):
        """
        Generate new view model

        Returns:
            A tuple (str,viewmodel) containing the `id` and `viewmodel.download_viewmodel.DownloadItemViewModel`

        """
        id_ = "DLVM" + ''.join(random.choices(string.ascii_letters, k=10))
        download_view_model = DownloadItemViewModel(model=DownloadModel(),
                                                    download_id=id_)
        self._active_item_view_models[id_] = download_view_model
        download_view_model.bind(finished_download=self._on_task_finished)
        return id_, download_view_model

    def _on_task_finished(self, item_view_model:DownloadItemViewModel|None, finished):
        """
        When a task is finished remove the view model from active list and update the queue

        Arguments:
            item_view_model : The view model
            finished (bool): Finished flag

        """
        if finished:
            cache_data = {
                "path": item_view_model.get_path(),
                "link": str(item_view_model.get_url()),
                "title": str(item_view_model.get_title()),
                "filetype": str(item_view_model.get_filetype()),
                "file_format": str(item_view_model.model.file_format),
                "date": str(datetime.datetime.now().strftime("%B %d, %Y"))
            }
            save_download_data(cache_data)

            self.remove_item_view_model(item_view_model.download_id)
            self.active_task_count -= 1
            if not self.silent_notification:
                self._notification_handler.post_notification(title="Download Manager",
                                                         message=f"Downloaded {item_view_model.get_path()}")
            # check for item in queue and download
            if not self.download_queue.empty():
                self.download_task = self.download_queue.get()
                self.active_task_count += 1

    def _on_task_failed(self, item_view_model:DownloadItemViewModel|None, failed):
        """
        Download has failed
        """
        if failed:
            self._notification_handler.post_notification(title="Download Manager",
                                                         message=f"Download failed{item_view_model.get_url()}")
            # check queue and update
            self.active_task_count -= 1
            if not self.download_queue.empty():
                self.download_task = self.download_queue.get()
                self.active_task_count += 1
