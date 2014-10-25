from . import state

class PathIterator:
    """ Base class representing a path.
    The class itself can be used as state of the current point,
    advanced by given time, or reset to the beginning of the path."""

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
        while True:
            yield self.state
            self.advance(dt)
