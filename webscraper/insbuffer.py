
class InsertBuffer:

    """Accumulate db records and insert them in batches"""

    def __init__(self, batch_size):
        self._batch_size = batch_size
        self._buf = []

    def add(self, obj):

        """Add one record to buffer"""

        self._buf.append(obj)

        if len(self._buf) >= self._batch_size:
            self.insert_batch()

    def insert_batch(self):

        """Remove one batch from buffer and insert to database"""

        chunk, self._buf = split_chunk(self._buf, self._batch_size)
        cls = type(chunk[0])
        cls.objects.bulk_create(chunk)


    def flush(self):

        """Insert all records from buffer to DB"""

        while self._buf:
            self.insert_batch()

    def __len__(self):
        return len(self._buf)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.flush()


def split_chunk(lst, size):

    """Cut a chunk from a list. Returns (chunk, remaining_list)"""

    l = len(lst)
    if l <= size:
        return lst, []
    else:
        return lst[:size], lst[size:]
