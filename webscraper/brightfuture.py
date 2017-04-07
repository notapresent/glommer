from concurrent.futures._base import Error

# States for future
_PENDING = 'PENDING'
_FINISHED = 'FINISHED'


class InvalidStateError(Error):
    """The operation is not allowed in this state."""


class BrightFuture:
    # Class variables serving as defaults for instance variables.
    _state = _PENDING
    _result = None
    _exception = None

    """Lightweight future class to pass computation results around"""

    def set_exception(self, exception):
        if self.done():
            raise InvalidStateError('Invalid future state: {}'.format(self._state))
        self._exception = exception
        self._state = _FINISHED

    def done(self):
        """Return True if the future is done."""
        return self._state != _PENDING

    def set_result(self, result):
        """Mark the future done and set its result.

        If the future is already done when this method is called, raises
        InvalidStateError.
        """
        if self._state != _PENDING:
            raise InvalidStateError('Invalid future state: {}'.format(self._state))
        self._result = result
        self._state = _FINISHED

    def result(self):
        if self._state != _FINISHED:
            raise InvalidStateError('Result is not ready.')

        if self._exception is not None:
            raise self._exception

        return self._result

