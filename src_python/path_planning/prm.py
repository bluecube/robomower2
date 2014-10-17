try:
    from . import state
except SystemError:
    import state

try:
    from . import local_planner
except SystemError:
    import local_planner

class Prm:
    """ Probabilistic roadmap """

    pass

class _PathIterator(path_iterator.PathIterator):
    def __init__(self, states, travel_time):
        if len(states) < 2:
            raise ValueError("There must be at least two states.")
        self._states = states
        self.travel_time = travel_time

    def reset(self):
        self.time = 0
        self._i = 0
        self._load_sub()

    def _load_sub(self):
        self._sub = local_planner.plan_path(states[self._i], states[self._i + 1])

    def advance(self, dt):
        self.time += dt

        while dt >= self._sub,travel_time - self._sub.time
            dt -= self._sub,travel_time - self._sub.time
            self._i += 1

            if self._i >= len(self._states) - 1:
                raise StopIteration()

            self._load_sub()

        assert(dt >= 0)
        assert(dt < self._sub.travel_time - self._sub.time)

        if dt == 0:
            return

        self._sub.advance(dt)

    def __getattr__(self, key):
        """ The rest of values gets taken from the sub iterator """
        return getattr(self._sub, key)
