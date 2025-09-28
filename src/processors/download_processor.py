import re
import threading
import time

from kivy.clock import Clock
from pytubefix import Stream

from src.core import logger, config
from collections import deque
from kivy.event import EventDispatcher
from kivy.properties import NumericProperty

from src.core.utils.utils import select_stream_quality, get_web_file_size
from src.viewmodels.album_viewmodel import AlbumViewModel
from src.viewmodels.download_viewmodel import DownloadViewModel
from src.viewmodels.notification_handler_vm import NotificationHandlerViewModel
from src.viewmodels.youtube_viewmodel import YouTubeViewModel
from src.views.Common.common_widgets import BaseQueryItem


class DownloadProcessor(EventDispatcher):

    max_item_units = NumericProperty(10, force_dispatch=True)
    max_processing_timeout = NumericProperty(10)  # seconds

    def __init__(self, notification_handler:NotificationHandlerViewModel=None,
                 youtube_view_model:YouTubeViewModel=None, album_view_model:AlbumViewModel=None,
                 download_view_model:DownloadViewModel=None, **kwargs):
        super().__init__(**kwargs)
        self._notification_handler = notification_handler
        self._youtube_view_model = youtube_view_model
        self._album_view_model = album_view_model
        self._download_view_model = download_view_model

        self.lock = threading.Lock()
        self.processing_queue = deque(maxlen=self.max_item_units)

        self.bind(max_item_units=self.on_max_processing_units)

    def process_item(self, widget:BaseQueryItem, mode="youtube", target_media="audio", mini_progress=False):
        """
        Process the item for download

        Arguments:
            widget (BaseQueryItem) : The widget that holds link data for processing
            mode (str) : Two modes supported for link processing 1. youtube 2. hiphopkit
            target_media: The media type audio/video for YouTube mode
            mini_progress (bool): Whether to show progress in the current widget
        """
        if len(self.processing_queue) == self.processing_queue.maxlen:
            self._notification_handler.post_notification(title="YouTube Video Processing" if mode == "youtube" else
                                                        "Song processing",
                                                         message="The processing queue is full wait before querying")
            return

        # check if link in queue and process
        link = widget.link
        if link in self.processing_queue:
            # post notification that the item is being processed
            self._notification_handler.post_notification(title="YouTube Video Processing" if mode == "youtube" else
                                                        "Song processing",
                                                         message="The item is processing please wait")
        else:
            # process the item
            self.processing_queue.append(link)
            view_model_id, view_model = self._download_view_model.generate_view_model()

            if mini_progress:
                widget.add_progress_container()
                # progress cont will be DownloadViewItemMini that has a view_model attribute that will be set here
                widget.progress_cont.view_model = view_model
                widget.progress_cont.status = "Getting link..."
            if widget.downloadable:
                if mini_progress:
                    widget.progress_cont.status = "Almost ready.."
                if mode == "youtube":
                    # we are dealing with CommonYouTubeItem | CommonYouTubeHttpResultItem
                    self._download_view_model.add_to_queue(
                        title=widget.title, link=widget.link,
                        type_=widget.stream_type, format_=widget.stream_format,
                        view_model_id=view_model_id
                    )
            else:
                # needs further processing
                def post_stream(widget_:BaseQueryItem, stream:Stream, dt):
                    if mini_progress:
                        widget_.progress_cont.status = "Almost ready.."
                    self._download_view_model.add_to_queue(
                        title=widget_.title, link=stream.url,
                        type_=stream.type, format_=stream.subtype,
                        view_model_id=view_model_id
                    )

                def post_http_item(f_link, f_title, f_format, f_type, _):
                    self._download_view_model.add_to_queue(
                        title=f_title, format_=f_format, link=f_link,
                        type_=f_type, view_model_id=view_model_id
                    )

                def mini_process(widget_:BaseQueryItem):
                    timeout = self.max_processing_timeout

                    with self.lock:
                        while True:
                            if timeout <= 0:
                                self.processing_queue.remove(widget_.link)
                                logger.warning(f"[DownloadProcessor] Discarding link: `{widget_.link}` Reason: Timeout")
                                self._notification_handler.post_notification(title="Download link processor",
                                                                             message=f"Discarding link: {widget_.link} "
                                                                                     f" Reason: Timeout")
                                # remove processed ite from queue
                                if widget_.link in self.processing_queue:
                                    self.processing_queue.remove(widget_.link)
                                break

                            try:
                                if mode == "youtube":
                                    streams = self._youtube_view_model.quick_search_url(widget_.link, audio_only=True if target_media == "audio" else None)
                                    if streams:
                                        if target_media == "audio":
                                            streams = streams.filter(only_audio=True)
                                            stream = select_stream_quality(streams)
                                        else:
                                            # get the specified quality
                                            streams = streams.filter(progressive=True)
                                            stream = select_stream_quality(streams, mode="video")

                                        Clock.schedule_once(lambda c: post_stream(widget_, stream, c), .005)
                                        if widget_.link in self.processing_queue:
                                            self.processing_queue.remove(widget_.link)
                                        break
                                elif mode == "hiphopkit":
                                    # the widget_ here will be SongViewCardItem, CommonSearchResult
                                    link_data = self._album_view_model.get_downloadable_link(widget_.link)
                                    if link_data:
                                        if mini_progress:
                                            widget_.progress_cont.status = "Validating link.."

                                        file_type = "Audio"
                                        file_format = "mp3"
                                        match widget_.type.lower():
                                            case "albums":
                                                file_format = "zip"
                                                file_type = "Zip"
                                            case "foreign":
                                                if re.search("album", widget_.title, re.I):
                                                    file_format = "zip"
                                                    file_type = "Zip"
                                                else:
                                                    file_format = "mp3"
                                                    file_type = "Audio"

                                        if mini_progress:
                                            widget_.progress_cont.status = "Almost ready.."
                                        Clock.schedule_once(
                                            lambda x: post_http_item(link_data.get('link'), widget_.title, file_format, file_type, x),
                                            0.01
                                        )
                                        # remove processed item in queue
                                        if widget_.link in self.processing_queue:
                                            self.processing_queue.remove(widget_.link)
                                        break

                            except Exception as e:
                                logger.info(f"[DownloadProcessor] Error `{e}` trials remaining {timeout}")
                                #raise e
                            timeout -= 1
                            time.sleep(1)

                threading.Thread(target=mini_process, args=(widget, ), daemon=True).start()

    def on_max_processing_units(self, _, units):
        """
        The maximum items that the queue will hold for processing
        Arguments:
            _ : instance of binder
            units (int): Maximum units for the processing queue

        """
        if units > 0:
            if units != self.processing_queue.maxlen:
                if len(self.processing_queue) >= units:
                    logger.info(f"[DownloadProcessor] The unit set for the queue is smaller than the current queue."
                                f" Some items may be lost. Skipping applying")
                    self._notification_handler.post_notification(title="Download Processor",
                                                                 message=f"The unit set for the queue is smaller than "
                                                                         f"the current queue. Some items may be lost."
                                                                         f" Skipping applying")
                else:
                    # copy the current queue to the new queue
                    queue_copy = self.processing_queue.copy()
                    self.processing_queue = deque(maxlen=units)
                    self.processing_queue.extend(queue_copy)
