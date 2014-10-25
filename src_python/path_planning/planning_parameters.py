import random
import math
from . import state

class PlanningParameters:
    """ This class is specific to robomower.
    Given configuration dict with limits and a map it calculates a cost of being
    in a path planning state."""

    def __init__(self, limits, world_map):
        self.max_velocity = limits["velocity"]
        self.max_tangential_acceleration = limits["acceleration"]
        self.max_radial_acceleration = limits["radial_acceleration"]
        self.max_jerk = limits["jerk"]
        self.max_angular_velocity = limits["angular_velocity"]
        self.world_map = world_map

    def state_cost(self, state):
        # Dynamic properties:

        velocity = state.velocity
        if abs(velocity) > self.max_velocity:
            print("too large velocity")
            return None

        angular_velocity = state.curvature * velocity
        if abs(angular_velocity) > self.max_angular_velocity:
            print("too large angular velocity")
            return None

        try:
            jerk = state.jerk
        except AttributeError:
            pass
        else:
            if abs(jerk) > self.max_jerk:
                print("too large jerk")
                return None

        radial_acceleration = angular_velocity * velocity
        normalized_acceleration = math.hypot(state.acceleration / self.max_tangential_acceleration,
                                             radial_acceleration / self.max_radial_acceleration)

        if normalized_acceleration > 1:
            print("too large normalized acceleration")
            return None

        # Map collisions:

        if self.world_map.has_collision(state.x, state.y):
            print("map collision")
            return None

        return 1

    def random_state(self):
        velocity = random.uniform(0, self.max_velocity)
        max_curvature = self.max_angular_velocity / velocity
        return state.State(random.uniform(0, 20),
                           random.uniform(0, 20),
                           random.uniform(0, 2 * math.pi),
                           velocity,
                           random.uniform(-self.max_tangential_acceleration,
                                          self.max_tangential_acceleration),
                           random.uniform(-max_curvature, max_curvature))
