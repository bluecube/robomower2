import logging
import path_planning
import math

class Controller:
    def __init__(self, drive, world_map, config):
        self._drive = drive
        self._world_map = world_map
        self._config = config
        self._logger = logging.getLogger(__name__)

        self.name = "Automatic mode" # for gui

        self._path_planning_parameters = path_planning.planning_parameters.PlanningParameters(config["limits"],
                                                                                              world_map,
                                                                                              drive.model)
        self._path_planner = path_planning.prm.Prm(self._path_planning_parameters)
        self._path = self._path_planner.plan_path(path_planning.simple_state(0, 0, 0),
                                            #path_planning.simple_state(12, 12, math.radians(90)))
                                            path_planning.simple_state(12, 15, math.radians(180)))


    def update(self, delta_t):
        self.forward = 0
        self.turn = 0
        if self._path:
            self._path.advance(delta_t)

            if self._path.finished():
                self._path = None
            else:
                self.forward = self._path.velocity
                self.turn = self.forward * self._path.curvature
        self._drive.set_command(self.forward, self.turn)

    @property
    def intended_state(self):
        return self._path
