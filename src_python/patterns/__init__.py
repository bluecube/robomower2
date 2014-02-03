import json
import math
import logging

class Pattern:
    logger = logging.getLogger(__name__)

    def __init__(self, filename, config):
        with open(filename, "r") as fp:
            self._pattern_iter = iter(json.load(fp))

        self._limits = config["limits"]
        self._next_part()

    def update(self, delta_t):
        current = self._current

        if current is None:
            return

        self._t += delta_t
        if self._t < self._t_a:
            self._value += self._a * delta_t
        elif self._t < self._t_a + self._t_v:
            self._value = self._v
        elif self._t < 2 * self._t_a + self._t_v:
            self._value -= self._a * delta_t
        else:
            self._value = 0
            self._next_part()

        if current["type"] == "line":
            self.forward = self._value
        elif current["type"] == "turn":
            self.turn = self._value

    def _next_part(self):
        try:
            self._current = next(self._pattern_iter)
        except StopIteration:
            self.logger.info("No more parts")
            self._current = None
            return

        if self._current["type"] == "line":
            self._a = self._limits["acceleration"]
            self._v = self._limits["velocity"]
            s = self._current["length"]
            self.logger.info("Line part, length %d", s)
        elif self._current["type"] == "turn":
            self._a = self._limits["angular_acceleration"]
            self._v = self._limits["angular_velocity"]
            s = math.radians(self._current["angle"])
            self.logger.info("Turn part, angle %d degrees", math.degrees(s))

        self._t_a, self._t_v = self._calc_times(self._a, self._v, s)
        self._t = 0
        self._value = 0

        self.forward = 0
        self.turn = 0


    def _calc_times(self, a, v, s):
        """ Calculate times to drive distance s with speed limit v and acceleration
        limit a. Returns tuple of time to accelerate / deccelerate and time to keep max speed"""

        t_a = self._limits["velocity"] / self._limits["acceleration"]
        s_a = v * t_a

        if 2 * s_a >= s:
            return (math.sqrt(s / a), 0)
        else:
            return (t_a, (s - s_a) / v)


