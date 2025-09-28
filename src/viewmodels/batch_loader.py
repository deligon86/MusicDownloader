from kivy.clock import Clock


class BatchLoader:

    def __init__(self, data_source, batch_size=10, on_batch=None, on_complete=None):
        """
        :param data_source:list|tuple  or function that returns a list|tuple
        :param batch_size: The number of items to query for loading
        :param on_batch: A function that will receive the batches for dispatch
        :param on_complete: A function that will be executed when the batching process is complete
        """

        self.data_source = data_source  # Callable or static list|tuple
        self.batch_size = batch_size
        self.on_batch = on_batch        # Callback to process each batch
        self.on_complete = on_complete  # Callback when done
        self.index = 0
        self.event = None

    def start(self, interval=10):
        self.index = 0
        self.event = Clock.schedule_interval(self._load_next_batch, interval)

    def _load_next_batch(self, dt):
        cache = self.data_source() if callable(self.data_source) else self.data_source
        if not cache or self.index >= len(cache):
            Clock.unschedule(self.event)
            if self.on_complete:
                self.on_complete()
            return

        next_index = min(self.index + self.batch_size, len(cache))
        batch = cache[self.index:next_index]
        if self.on_batch:
            self.on_batch(batch)
        self.index = next_index
