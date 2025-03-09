import threading


class CustomThread(threading.Thread):
    def __init__(self, target=None, name=None, args=()):
        """
        A custom threading class that utilizes native threading mechanisms

        :param target: Target function to execute in the thread.
        :param name: Name of the thread.
        """
        super().__init__(name=name)
        self._stop_event = threading.Event()  # Event to signal thread termination
        self._target = target
        self._args = args

    def stop(self):
        """
        Sets the stop event to signal the thread to stop execution
        :return
        """
        self._stop_event.set()

    def stopped(self):
        """
        Returns whether the stop event has been triggered
        :return
        """
        return self._stop_event.is_set()

    def run(self):
        """
        Override the run method to execute the target unless stopped
        :return
        """
        if self._target and not self.stopped():
            self._target(*self._args)
