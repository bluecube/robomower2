import random
import math
import util.halton
import differential_drive
from . import state

class PlanningParameters:
    """ This class is specific to robomower.
    Given configuration dict with limits and a map it calculates a cost of being
    in a path planning state."""

    def __init__(self, limits, world_map, drive_model):
        self.max_velocity = limits["velocity"]
        self.max_tangential_acceleration = limits["acceleration"]
        self.max_radial_acceleration = limits["radial_acceleration"]
        self.max_jerk = limits["jerk"]
        self.max_angular_velocity = limits["angular_velocity"]
        self.min_wheel_speed = limits["min_wheel_speed"]
        self.world_map = world_map
        self._halton = util.halton.HaltonSequence(4)
        self._drive_model = drive_model

    def state_cost(self, state):
        # Dynamic properties:

        velocity = state.velocity
        if abs(velocity) > self.max_velocity:
            return None

        angular_velocity = state.curvature * velocity
        if abs(angular_velocity) > self.max_angular_velocity:
            return None

        try:
            jerk = state.jerk
        except AttributeError:
            pass
        else:
            if abs(jerk) > self.max_jerk:
                return None

        radial_acceleration = angular_velocity * velocity
        normalized_acceleration = math.hypot(state.acceleration / self.max_tangential_acceleration,
                                             radial_acceleration / self.max_radial_acceleration)

        if normalized_acceleration >= 1:
            return None

        # Map collisions:

        if self.world_map.has_collision(state.x, state.y):
            return None

        cost = 1 / (1 - normalized_acceleration)

        ticks_left, ticks_right = self._drive_model.velocity_to_ticks(velocity, angular_velocity)

        if abs(ticks_left) < self.min_wheel_speed or abs(ticks_right) < self.min_wheel_speed:
            cost *= 2

        return cost

    def random_state(self):
        val = next(self._halton)

        velocity = self.max_velocity * val[0]
        max_curvature = self.max_angular_velocity / velocity
        return state.State(30 * val[1] - 10,
                           30 * val[2] - 10,
                           2 * math.pi * val[3],
                           velocity,
                           0,
                           0)
