from . import state

class PathIterator:
    """ Base class representing a path.
    The class itself can be used as state of the current point,
    advanced by given time, or reset to the beginning of the path."""

    def __init__(self):
        self.reset()

    def reset(self):
        raise NotImplementedError()

    def jump_to(self, time):
        if (time > self.time):
            self.advance(time - self.time)
        else:
            self.reset()
            self.advance(time)

    def advance(self, dt):
        raise NotImplementedError()

    def sample_intervals(self, dt):
        self.reset()
        while not self.finished():
            yield (self.x, self.y)
            self.advance(dt)
        yield (self.x, self.y)

    def finished(self):
        """ Return True if the path is at the end. """
        raise NotImplementedError()
