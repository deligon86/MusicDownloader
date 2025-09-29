import os
import subprocess
import time
import asyncio
import aiohttp
import pathlib
import datetime
import aiofiles
import requests
from typing import Optional, Dict, Any
from src.core import logger
from src.core.utils.utils import sanitize_filename
from src.core.utils.customthread import CustomThread
from src.core.utils.utils import get_remote_file_size
from kivy.clock import Clock, mainthread
from kivy.utils import platform
from kivy.event import EventDispatcher
from kivy.properties import (
    StringProperty, NumericProperty, BooleanProperty
)


class DownloadModel(EventDispatcher):
    """
    Manages file downloads with support for both synchronous and asynchronous operations.
    Provides progress tracking, pause/resume functionality, and error handling.
    """
    
    # Kivy Properties
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

    # Constants
    MIN_DELAY = 0.001  # 1ms minimum delay for UI updates
    CHUNK_SIZE = 8192  # 8KB chunks for better performance
    DOWNLOAD_TIMEOUT = 30
    FILE_WAIT_TIMEOUT = 5.0
    FILE_WAIT_INTERVAL = 0.2

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._initialize_state()

    def _initialize_state(self):
        """Initialize all instance variables to their default states."""
        self.url: Optional[str] = None
        self.title: Optional[str] = None
        self.download_file_path: Optional[str] = None
        self.file_type: Optional[str] = None
        self.file_size: Optional[int] = None
        self.file_format: Optional[str] = None
        self.bytes_downloaded: int = 0
        self.downloading: bool = False
        self.download_thread: Optional[CustomThread] = None
        self.in_simulation: bool = False
        self._task: Optional[asyncio.Task] = None
        self._session: Optional[aiohttp.ClientSession] = None

    def set_variables(self, title: str, link: str, file_type: str, 
                     file_format: str, download_location: str, 
                     simulated: bool = False) -> None:
        """
        Configure download parameters and initialize download process.

        Args:
            title: File title/name
            link: Download URL
            file_type: Type of file (Audio/Video/Zip)
            file_format: File extension
            download_location: Directory to save the file
            simulated: Enable simulation mode for testing
        """
        self._reset_state()
        
        self.url = link
        self.title = title
        self.file_type = file_type.capitalize()
        self.file_format = file_format.lower()
        self.in_simulation = simulated
        
        self._setup_file_path(download_location)
        self._determine_file_size()
        self._trigger_download_start()

    def _reset_state(self):
        """Reset the download state for a new download."""
        self.bytes_downloaded = 0
        self.progress_value = 0
        self.download_failed = False
        self.finished_download = False
        self.cancelled = False
        self.paused = False
        self.error = ""
        self.status = ""

    def _setup_file_path(self, download_location: str):
        """Set up the complete file path for download."""
        sanitized_title = sanitize_filename(self.title).strip()
        filename = f"{sanitized_title}.{self.file_format}.fdl"
        
        download_path = pathlib.Path(download_location)
        download_path.mkdir(parents=True, exist_ok=True)
        
        self.download_file_path = str((download_path / filename).resolve())

    def _determine_file_size(self):
        """Determine the remote file size if not in simulation mode."""
        if not self.in_simulation and self.url:
            self.file_size = get_remote_file_size(self.url, "bytes")
            if not self.file_size:
                self._schedule_ui_update("size_indeterminable", True)

    def _trigger_download_start(self):
        """Schedule the download start on the UI thread."""
        self._schedule_ui_update("variables_set", True)

    def start_download_thread(self, resume: bool = False, mode: str = "wb") -> None:
        """
        Start download in a background thread.

        Args:
            resume: Whether to resume a previous download
            mode: File write mode ('wb' for new, 'ab' for resume)
        """
        self.waiting_for_download = False
        
        target_func = self.simulate_download if self.in_simulation else self.download
        self.download_thread = CustomThread(
            target=target_func, 
            args=(resume, mode),
            daemon=True
        )
        self.download_thread.start()

    def stop_download_thread(self) -> None:
        """Safely stop the download thread."""
        if self.download_thread and self.download_thread.is_alive():
            self.download_thread.stop()
            self.download_thread.join(timeout=2.0)

    async def start_download_async(self, resume: bool = False, mode: str = "wb") -> None:
        """
        Start asynchronous download.

        Args:
            resume: Whether to resume a previous download
            mode: File write mode
        """
        if self._task and not self._task.done():
            self._task.cancel()

        self._task = asyncio.create_task(self.download_async(resume, mode))

    def stop_download_async(self) -> None:
        """Cancel asynchronous download and clean up."""
        if self._task:
            self._task.cancel()
            self._task = None
        
        if self._session:
            asyncio.create_task(self._session.close())
            self._session = None
            
        self.clean_files()

    def download(self, resumed: bool = False, mode: str = "wb") -> None:
        """
        Perform synchronous file download.

        Args:
            resumed: Whether this is a resumed download
            mode: File write mode
        """
        try:
            headers = self._build_headers(resumed)
            downloaded = self.bytes_downloaded if resumed else 0
            
            self._ensure_download_directory()
            self._update_initial_status(downloaded)

            with requests.get(self.url, stream=True, headers=headers, 
                            timeout=self.DOWNLOAD_TIMEOUT) as response:
                response.raise_for_status()
                self._process_download_stream(response, downloaded, mode)

        except Exception as e:
            self._handle_download_error(e)

    def _build_headers(self, resumed: bool) -> Dict[str, str]:
        """Build HTTP headers for the request."""
        if resumed and self.bytes_downloaded > 0:
            return {'Range': f'bytes={self.bytes_downloaded}-'}
        return {}

    def _ensure_download_directory(self):
        """Ensure the download directory exists."""
        download_dir = pathlib.Path(self.download_file_path).parent
        download_dir.mkdir(parents=True, exist_ok=True)

    def _update_initial_status(self, downloaded: int):
        """Update the initial download status."""
        if self.file_size:
            status = f"{self._format_size(downloaded)}/{self._format_size(self.file_size)}"
            self._set_status(status)

    def _process_download_stream(self, response: requests.Response, 
                               downloaded: int, mode: str):
        """Process the download stream and write to file."""
        path = pathlib.Path(self.download_file_path)
        
        with path.open(mode) as file:
            for chunk in response.iter_content(chunk_size=self.CHUNK_SIZE):
                if self._should_stop_download():
                    break
                    
                file.write(chunk)
                downloaded += len(chunk)
                self._update_progress(downloaded)

        if not self._should_stop_download():
            self._finalize_download(path)

    def _should_stop_download(self) -> bool:
        """Check if download should be stopped."""
        return self.paused or self.cancelled

    def _update_progress(self, downloaded: int):
        """Update download progress and status."""
        self.bytes_downloaded = downloaded
        
        if self.file_size and self.file_size > 0:
            progress = min(100, (downloaded / self.file_size) * 100)
            self._set_progress(progress)
            
            status = f"{self._format_size(downloaded)}/{self._format_size(self.file_size)}"
            self._set_status(status)
        else:
            self._set_progress(1)  # Indeterminate progress

    def _finalize_download(self, path: pathlib.Path):
        """Finalize download after completion."""
        if self._wait_for_file(path):
            self.rename_on_complete()
            self._set_finished_download(True)
        else:
            self._set_download_failed("Download completed but file is empty or missing")

    async def download_async(self, resumed: bool = False, mode: str = "wb") -> None:
        """
        Perform asynchronous file download.

        Args:
            resumed: Whether this is a resumed download
            mode: File write mode
        """
        try:
            headers = self._build_headers(resumed)
            downloaded = self.bytes_downloaded if resumed else 0

            async with aiohttp.ClientSession() as self._session:
                async with self._session.get(self.url, headers=headers) as response:
                    if response.status != 200 and response.status != 206:
                        self._set_download_failed(f"HTTP Error: {response.status}")
                        return

                    async with aiofiles.open(self.download_file_path, mode=mode) as file:
                        async for chunk in response.content.iter_chunked(self.CHUNK_SIZE):
                            if self.cancelled:
                                self._set_download_failed("Download cancelled")
                                return
                            if self.paused:
                                self._set_status("Paused")
                                return
                                
                            await file.write(chunk)
                            downloaded += len(chunk)
                            self._update_progress_async(downloaded)

            self._set_finished_download(True)

        except asyncio.CancelledError:
            self._set_status("Download cancelled")
        except Exception as e:
            self._set_download_failed(f"Download error: {e}")

    def _update_progress_async(self, downloaded: int):
        """Update progress for async downloads."""
        self.bytes_downloaded = downloaded
        
        if self.file_size and self.file_size > 0:
            progress = min(100, int(downloaded / self.file_size) * 100)
            self.progress_value = progress
            
            status = f"{self._format_size(downloaded)}/{self._format_size(self.file_size)}"
            self.status = status

    @staticmethod
    def _format_size(bytes_size: int) -> str:
        """Format file size in human-readable format."""
        if bytes_size == 0:
            return "0 B"
            
        units = ['B', 'KB', 'MB', 'GB']
        unit_index = 0
        
        while bytes_size >= 1024 and unit_index < len(units) - 1:
            bytes_size /= 1024.0
            unit_index += 1
            
        return f"{bytes_size:.2f} {units[unit_index]}"

    @staticmethod
    def _wait_for_file(path: pathlib.Path, timeout: float = None, 
                      interval: float = None) -> bool:
        """
        Wait for file to appear on disk with content.

        Args:
            path: File path to check
            timeout: Maximum time to wait
            interval: Check interval

        Returns:
            True if file exists with content, False otherwise
        """
        timeout = timeout or DownloadModel.FILE_WAIT_TIMEOUT
        interval = interval or DownloadModel.FILE_WAIT_INTERVAL
        
        start = time.time()
        while time.time() - start < timeout:
            if path.exists() and path.stat().st_size > 0:
                return True
            time.sleep(interval)
        return False

    # UI Control Methods
    def pause_download(self) -> None:
        """Pause the current download."""
        self._schedule_ui_update("paused", True)

    def cancel_download(self) -> None:
        """Cancel the current download."""
        self._schedule_ui_update("cancelled", True)

    def resume_download(self) -> None:
        """Resume a paused download."""
        self._schedule_ui_update("paused", False)

    def retry_download(self) -> None:
        """Retry the failed download."""
        mode = "ab" if pathlib.Path(self.download_file_path).exists() else "wb"
        self.start_download_thread(mode=mode)

    @mainthread
    def _set_progress(self, value: float) -> None:
        """Set progress value on main thread."""
        self.progress_value = value

    @mainthread
    def _set_status(self, status: str) -> None:
        """Set status text on main thread."""
        self.status = status

    @mainthread
    def _set_finished_download(self, value: bool) -> None:
        """Set finished_download property on main thread."""
        self.finished_download = value

    @mainthread
    def _set_download_failed(self, error_message: str) -> None:
        """Set download failed state on main thread."""
        self.download_failed = True
        self.error = error_message

    def _schedule_ui_update(self, property_name: str, value: Any) -> None:
        """Schedule a UI property update on the main thread."""
        Clock.schedule_once(lambda dt: setattr(self, property_name, value), self.MIN_DELAY)

    def _handle_download_error(self, error: Exception) -> None:
        """Handle download errors consistently."""
        error_mapping = {
            requests.exceptions.RequestException: f"Network error: {error}",
            IOError: f"File I/O error: {error}",
            OSError: f"System error: {error}"
        }
        
        error_message = error_mapping.get(type(error), f"Unexpected error: {error}")
        self._set_download_failed(error_message)

    def clean_files(self) -> None:
        """Remove incomplete download files."""
        try:
            path = pathlib.Path(self.download_file_path)
            if path.exists():
                path.unlink()
                logger.info(f"Cleaned download file: {self.download_file_path}")
        except Exception as e:
            logger.warning(f"Could not clean file {self.download_file_path}: {e}")

    def rename_on_complete(self, new_extension: Optional[str] = None, 
                          add_timestamp: bool = False) -> bool:
        """
        Rename downloaded file to its final name.

        Args:
            new_extension: Custom file extension
            add_timestamp: Add timestamp to avoid conflicts

        Returns:
            True if rename successful, False otherwise
        """
        try:
            current_path = pathlib.Path(self.download_file_path)
            
            # Determine new path
            if new_extension:
                new_path = current_path.with_suffix(new_extension)
            else:
                new_path = current_path.with_suffix('')  # Remove .fdl extension

            # Handle file conflicts
            if new_path.exists():
                if add_timestamp:
                    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
                    new_path = new_path.parent / f"{new_path.stem}_{timestamp}{new_path.suffix}"
                else:
                    logger.warning(f"File already exists: {new_path}")
                    return False

            # Perform rename
            current_path.rename(new_path)
            self.download_file_path = str(new_path)
            
            logger.info(f"Successfully renamed to: {self.download_file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to rename file: {e}")
            return False

    def show_file(self) -> None:
        """Open file location in system file manager."""
        if platform == "win" and self.download_file_path:
            try:
                path = pathlib.Path(self.download_file_path)
                if path.exists():
                    subprocess.run(['explorer', '/select,', str(path)], check=False)
            except Exception as e:
                logger.warning(f"Could not show file: {e}")

    def simulate_download(self, *args) -> None:
        """Simulate download for testing UI components."""
        total_steps = 100
        for progress in range(1, total_steps + 1):
            if self.cancelled:
                break
                
            self._set_progress(progress)
            time.sleep(0.01)  # 10ms delay between updates

        if not self.cancelled:
            self._set_finished_download(True)