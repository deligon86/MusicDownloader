import threading
import traceback
from typing import Callable, Any, Optional


class CustomThread(threading.Thread):

    def __init__(self, target: Optional[Callable] = None, name: Optional[str] = None,
                 args: tuple = (), kwargs: Optional[dict] = None,
                 error_callback: Optional[Callable] = None):
        """
        A custom threading class with proper error handling and stop mechanism

        Arguments:
            target: Target function to execute in the thread
            name: Name of the thread
            args: Arguments for the target function
            kwargs: Keyword arguments for the target function
            error_callback: Callback function to handle errors (receives exception)
        """
        super().__init__(name=name)
        self._stop_event = threading.Event()
        self._target = target
        self._args = args or ()
        self._kwargs = kwargs or {}
        self._error_callback = error_callback
        self._exception = None

    def stop(self):
        """Signal the thread to stop execution"""
        self._stop_event.set()

    def stopped(self):
        """Check if stop has been requested"""
        return self._stop_event.is_set()

    def get_exception(self):
        """Get any exception that occurred during execution"""
        return self._exception

    def run(self):
        """
        Override the run method with proper error handling and stop checking
        """
        try:
            if self._target and not self.stopped():
                # Pass the stop_check function to the target if it accepts it
                if callable(self._target):
                    # Check if target function accepts a stop_check parameter
                    import inspect
                    sig = inspect.signature(self._target)
                    if 'stop_check' in sig.parameters:
                        self._target(*self._args, stop_check=self.stopped, **self._kwargs)
                    else:
                        self._target(*self._args, **self._kwargs)
        except Exception as e:
            self._exception = e
            # Log the error
            print(f"Thread {self.name} failed with error: {e}")
            traceback.print_exc()

            # Call error callback if provided
            if self._error_callback:
                self._error_callback(e)

