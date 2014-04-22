import util

class _DriveProxy:
    def __init__(self, parent):
        self._parent = parent
        self._command = 0
        self.PID_FREQUENCY = 50

    def update(self, command):
        previous = self._command
        self._command = command
        return {"distance": round(previous * self.PID_FREQUENCY * self._parent._elapsed)}

    def params(self, *args, **kwargs):
        pass

class _Broadcasts:
    def __init__(self, parent):
        self._parent = parent

    def latch_values(self):
        self._parent._latch_values()

class MockHw:
    def __init__(self):
        self._timer = util.TimeElapsed()
        self._elapsed = None

        self.broadcast = _Broadcasts(self)
        self.left = _DriveProxy(self)
        self.right = _DriveProxy(self)

    def _latch_values(self):
        self._elapsed = self._timer()
