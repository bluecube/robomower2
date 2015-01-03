import logging
import path_planning
import math

class Controller:
    def __init__(self, drive, world_map, config):
        self._drive = drive
        self._world_map = world_map
        self._config = config
        self._logger = logging.getLogger(__name__)

        self.name = "Path following" # for gui

        self._forward_factor = config["path_following"]["forward_factor"]
        self._side_factor = config["path_following"]["side_factor"]
        self._turn_factor = config["path_following"]["turn_factor"]

        self._path_planning_parameters = path_planning.planning_parameters.PlanningParameters(config["limits"],
                                                                                              world_map,
                                                                                              drive.model)
        self._path_planner = path_planning.prm.Prm(self._path_planning_parameters)
        self._path = self._path_planner.plan_path(path_planning.simple_state(0, 0, 0),
                                            #path_planning.simple_state(12, 12, math.radians(90)))
                                            path_planning.simple_state(12, 15, math.radians(0)))

    def update(self, current_state, delta_t):
        self.forward = 0
        self.turn = 0
        if self._path:
            self._path.advance(delta_t)

            if self._path.finished():
                self._path = None
            else:
                self.forward = self._path.velocity
                self.turn = self.forward * self._path.curvature

                self._corrections(current_state)

        self._drive.set_command(self.forward, self.turn)

    def _corrections(self, actual_state):
        dx = self._path.x - actual_state.x
        dy = self._path.y - actual_state.y

        c = math.cos(actual_state.heading)
        s = math.sin(actual_state.heading)

        forward_error = c * dx + s * dy
        side_error    = - s * dx + c * dy
        turn_error    = self._path.heading - actual_state.heading

        self.forward += forward_error * self._forward_factor
        self.turn += side_error * self._side_factor + turn_error * self._turn_factor

    @property
    def intended_state(self):
        if self._path is None:
            return None
        else:
            return self._path.as_state()
