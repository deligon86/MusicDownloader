import os
import subprocess
import time
import asyncio
import aiohttp
import pathlib
import datetime
import aiofiles
import requests
from src.core import logger
from src.core.utils.utils import set_variable
from src.core.utils.utils import sanitize_filename
from src.core.utils.customthread import CustomThread
from src.core.utils.utils import get_web_file_size
from kivy.clock import Clock
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.properties import (
    StringProperty, NumericProperty,
    BooleanProperty
)


def wait_for_file(path, timeout=5.0, interval=0.2):
    """
    Waits for a file to appear on disk, retrying for up to `timeout` seconds.
    """
    start = time.time()
    while time.time() - start < timeout:
        if path.exists() and path.stat().st_size > 0:
            return True
        time.sleep(interval)
    return False


class DownloadModel(EventDispatcher):
    waiting_for_download = BooleanProperty(defaultvalue=False)
    finished_download = BooleanProperty(defaultvalue=False, force_dispatch=True)
    paused = BooleanProperty(defaultvalue=False)
    progress_value = NumericProperty(force_dispatch=True)
    cancelled = BooleanProperty(defaultvalue=False, force_dispatch=True)
    variables_set = BooleanProperty(False, force_dispatch=True)
    size_indeterminable = BooleanProperty(False, force_dispatch=True)
    download_failed = BooleanProperty(False, force_dispatch=True)
    error = StringProperty(force_dispatch=True)
    status = StringProperty(force_dispatch=True)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.url =None
        self.title = None
        self.download_file_path = None
        self.file_type = None
        self.file_size = None
        self.file_format = None
        self.bytes_downloaded = 0
        self.downloading = False
        self.download_thread = None
        self.in_simulation = False

        self.delay = 0.001  # 1ms Minimum delay for transmitting messages
        self._task = None

    def set_variables(self, title, link, file_type, file_format, download_location, simulated=False):
        """
        Set the variables necessary for download. This will trigger the download

        :param title: title of the file
        :param link: download link
        :param file_type: Audio/Video/Zip
        :param file_format: file extension
        :param download_location: download path
        :param simulated  : For development testing of widgets behavior
        :return:
        """
        self.url = link
        self.title = title
        self.file_type = file_type.capitalize()
        self.file_format = file_format
        self.bytes_downloaded = 0
        self.download_file_path = str(pathlib.Path(os.path.join(download_location, f"{sanitize_filename(title).strip()}.{file_format.lower()}.fdl")).resolve())
        self.in_simulation = simulated
        if not simulated:
            self.file_size = get_web_file_size(link, "bytes")
            if self.file_size == 0:
                Clock.schedule_once(lambda c: set_variable(self, "size_indeterminable", True, c), self.delay)  # To use the progressbar loop

        # trigger download
        Clock.schedule_once(lambda c: set_variable(self, "variables_set", True, c), self.delay)

    def start_download_thread(self, resume=False, mode="wb"):
        """
        Start downloading in a thread

        :param resume: In resume or a fresh download
        :param mode: File writing mode
        """
        function = self.download
        self.waiting_for_download = False
        if self.in_simulation:
            function = self.simulate_download
        self.download_thread = CustomThread(target=function, args=(resume, mode))
        self.download_thread.daemon = True
        self.download_thread.start()

    def stop_download_thread(self):
        """
        Stop download thread
        :return:
        """
        if self.download_thread:
            if not self.download_thread.stopped():
                self.download_thread.stop()
                self.download_thread.join()

    async def start_download_async(self, resume=False, mode="wb"):
        """
        Start downloading using async
        """
        async def start_task():
            task = asyncio.create_task(self.download_async(resume, mode))
            return task
        self._task = await start_task()

    def stop_download_async(self):
        """
        Stod download in async mode
        """
        if self._task:
            self._task.cancel()
        self.clean_files()

    def download(self, resumed=False, mode="wb"):
        """
        Download the file

        :param resumed: whether this is a resumed download
        :param mode: file write mode
        """
        downloaded = self.bytes_downloaded if resumed else 0.000001
        headers = {}

        if resumed:
            headers = {'Range': f'bytes={self.bytes_downloaded}-'}  # Correct header name and format
            downloaded = self.bytes_downloaded

        # Update initial status
        Clock.schedule_once(
            lambda c: self.set_status(
                f"{round(downloaded / (1024 * 1024), 2)}Mb/{round(self.file_size / (1024 * 1024), 2)}Mb", c),
            0
        )

        try:
            # Ensure directory exists
            download_dir = os.path.dirname(self.download_file_path)
            if download_dir and not os.path.exists(download_dir):
                os.makedirs(download_dir, exist_ok=True)

            path = pathlib.Path(self.download_file_path)
            # Use context manager for both request and file handling
            with requests.get(self.url, stream=True, headers=headers, timeout=30) as response:
                response.raise_for_status()  # This will raise an exception for 4xx/5xx responses

                with path.open(mode) as out_file:
                    for chunk in response.iter_content(chunk_size=2048):
                        if self.paused:
                            break

                        if self.cancelled:
                            self.clean_files()
                            break

                        #if chunk:  # Filter out keep-alive chunks
                        out_file.write(chunk)
                        #out_file.flush()  # Force write to disk
                        downloaded += len(chunk)

                        try:
                            progress_value = round(downloaded / self.file_size * 100, 0)
                            Clock.schedule_once(lambda c: self.set_progress(progress_value, c), self.delay)
                            Clock.schedule_once(lambda c: self.set_status(
                                f"{round(downloaded / (1024 * 1024), 2)}Mb/{round(self.file_size / (1024 * 1024), 2)}Mb",
                                c),
                                                self.delay
                                                )
                        except ZeroDivisionError:
                            Clock.schedule_once(lambda c: self.set_progress(1, c), self.delay)

            # Verify the download completed successfully
            if not self.paused and not self.cancelled:
                # Check if file actually exists and has content
                if wait_for_file(path):
                    self.rename_on_complete()
                    Clock.schedule_once(lambda c: set_variable(self, "finished_download", True, c), self.delay)
                else:
                    error = "Download completed but file is empty or missing"
                    Clock.schedule_once(lambda c: set_variable(self, "download_failed", True, c), self.delay)
                    Clock.schedule_once(lambda c: set_variable(self, "error", error, c), self.delay)

        except requests.exceptions.RequestException as e:
            error = f"Network error: {str(e)}"
            Clock.schedule_once(lambda c: set_variable(self, "download_failed", True, c), self.delay)
            Clock.schedule_once(lambda c: set_variable(self, "error", error, c), self.delay)
        except IOError as e:
            error = f"File I/O error: {str(e)}"
            Clock.schedule_once(lambda c: set_variable(self, "download_failed", True, c), self.delay)
            Clock.schedule_once(lambda c: set_variable(self, "error", error, c), self.delay)
        except Exception as e:
            error = f"Unexpected error: {str(e)}"
            Clock.schedule_once(lambda c: set_variable(self, "download_failed", True, c), self.delay)
            Clock.schedule_once(lambda c: set_variable(self, "error", error, c), self.delay)

    async def download_async(self, resumed=False, mode="wb"):
        """
        Download asynchronously

        """
        downloaded = 0.000001  # avoid ZeroDivisionError if size is not determined
        headers = {}
        if resumed:
            headers = {'bytes-range': self.bytes_downloaded}
            # recalculate progress
            downloaded = self.bytes_downloaded

        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url, headers=headers) as res:
                    if res.status != 200:
                        self.status = "Failed with code: " + str(res.status)
                        self.error = self.status
                        self.download_failed = True
                        return
                    async with aiofiles.open(self.download_file_path, mode=mode) as out_file:
                        async for chunk in res.content.iter_chunked(10240):
                            if self.cancelled:
                                self.status = "Cancelled"
                                self.download_failed = True
                                return
                            if self.paused:
                                self.status = "Paused"
                                return
                            await out_file.write(chunk)
                            downloaded += len(chunk)
                            self.progress_value = downloaded / self.file_size * 100 if self.file_size else 0
                            self.status = f"{round(downloaded/(1024*10240), 2)}Mb/{round(self.file_size/(1024*1024), 2)}Mb"
            self.finished_download = True
        except Exception as e:
            error = f"Download error: {e}"
            self.error = error
            self.download_failed = True

    def pause_download(self):
        Clock.schedule_once(lambda c: set_variable(self, "paused", True, c), .001)

    def cancel_download(self):
        Clock.schedule_once(lambda c: set_variable(self, "cancelled", True, c), .001)

    def resume_download(self):
        Clock.schedule_once(lambda c: set_variable(self, "paused", False, c), .001)

    def set_progress(self, value, dt=None):
        self.progress_value = value
        #print("\r Set progress: {}".format(value), end="", flush=True)

    def set_status(self, status, _):
        """
        :param status:
        :param _:
        :return:
        """
        self.status = status

    def retry_download(self):
        path = os.path.split(self.download_file_path)
        if path[1] in os.listdir(path[0]):
            mode = "ab"
        else:
            mode = "wb"

        self.start_download_thread(mode=mode)

    def clean_files(self):
        """
        Remove file residues
        """
        try:
            os.remove(self.download_file_path)
        except Exception as e:
            logger.warning(f"[DownloadModel] Could not clean file {self.download_file_path} Error, {e}")

    def rename_on_complete(self, new_extension=None, add_timestamp=False):
        """
        Rename the file on complete

        :param new_extension: Custom extension to use (e.g., ".mp4", ".mp3")
        :param add_timestamp: Whether to add timestamp to avoid conflicts
        :return: True if successful, False otherwise
        """
        try:
            download_path = pathlib.Path(self.download_file_path)

            # Determine new filename
            if new_extension:
                # Use custom extension
                new_path = download_path.with_suffix(new_extension)
            else:
                # Remove extension (or use your specific logic)
                new_path = download_path.with_suffix('')

            # Handle filename conflicts
            if new_path.exists():
                if add_timestamp:
                    # Add timestamp to make filename unique
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_path = new_path.parent / f"{new_path.stem}_{timestamp}{new_path.suffix}"
                else:
                    logger.warning(f"[Rename] Target file exists, not overwriting `{new_path}`")
                    return False

            # Perform the rename operation
            download_path.rename(new_path)

            # Verify rename operation
            if new_path.exists() and not download_path.exists():
                self.download_file_path = str(new_path)
                logger.info(f"[Rename] Successfully renamed to `{self.download_file_path}`")
            else:
                logger.error(f"[Rename] Rename operation failed verification")

        except Exception as e:
            logger.error(f"[Rename] Error `{e}`")

    def show_file(self):
        """
        Show the file in folder
        :return:
        """
        try:
            if platform == "win":
                subprocess.run(['explorer', '/select,', self.download_file_path])
        except:
            pass


    def simulate_download(self, *args):
        total = 101
        limit = 100
        for n in range(1, total):
            Clock.schedule_once(lambda c: set_variable(self, "progress_value",
                                                       n, c), 2 / 1000)
            if n == limit:
                Clock.schedule_once(lambda c: set_variable(self, "finished_download",
                                                           True, c), 2 / 1000)
            time.sleep(10/1000)  # milliseconds

