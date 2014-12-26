import pygame
import logging
import math
from . import config
from . import widgets
from . import mapwidget
from . import controller

pygame.init()

class Gui:
    grid_cell_size = 150
    grid_columns = 2
    grid_width = grid_columns * grid_cell_size

    def _set_mode(self, size = (0, 0)):
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)

    def __init__(self, robot_config):
        self._logger = logging.getLogger(__name__)

        self._set_mode()

        lim = robot_config["limits"]
        self._config = robot_config

        self.finished = False

        self.controller = None

        self._velocity = widgets.Dial("velocity", 0, math.ceil(lim["velocity"] * 12) / 10, "%.1f", "%.2f", "m/s")
        self._load = widgets.Dial("CPU load", 0, 100, "%d", "%d", "%")
        self._drive = widgets.Xy("",
                                 -lim["angular_velocity"],
                                 lim["velocity"],
                                 "%.2f rad/s", "%.2f m/s")
        self._p_slider = widgets.Slider("kP", 0, 128, "%.1f")
        self._i_slider = widgets.Slider("kI", 0, 128, "%.1f")
        self._d_slider = widgets.Slider("kD", 0, 128, "%.1f")
        self._pid_grid = widgets.Grid(3, [self._p_slider, self._i_slider, self._d_slider], 10)
        self._rpm_r = widgets.Dial("R", 0, 12, "%.0f", "%.1f", "kRPM")
        self._rpm_l = widgets.Dial("L", 0, 12, "%.0f", "%.1f", "kRPM")
        self._rpm_grid = widgets.Grid(2, [self._rpm_l, self._rpm_r], 5)

        self._grid = widgets.Grid(self.grid_columns,
                                  [self._velocity, self._drive, self._load, self._pid_grid,
                                   self._rpm_grid],
                                  5)
        self._map = mapwidget.MapWidget(robot_config["gui"]["map_zoom"])

        self._log_widget = widgets.LogWidget(True)
        self._log_widget.setFormatter(logging.Formatter("%(asctime)s %(name)s: %(message)s", "%H:%M:%S"))
        logging.getLogger().addHandler(self._log_widget)

        self._logger.info("GUI ready")

    def draw(self):
        w, h = self.screen.get_size()

        self.screen.fill(config.bgcolor)


        self._grid.draw(self.screen,
                        w - self.grid_width, 0,
                        self.grid_width, self._grid.rows * self.grid_cell_size,
                        self._mouse)
        self._log_widget.draw(self.screen,
                              0, h * 0.7,
                              w - self.grid_width, h * 0.3,
                              self._mouse)
        self._map.draw(self.screen,
                       0, 0,
                       w - self.grid_width, h,
                       self._mouse)

    def update(self):
        self._mouse = None
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.finished = True
                return
            elif event.type == pygame.VIDEORESIZE:
                self._set_mode(event.size)
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 4:
                    self._map.zoom(1)
                elif event.button == 5:
                    self._map.zoom(-1)
            elif event.type == pygame.MOUSEMOTION:
                if event.buttons[0]:
                    self._mouse = event.pos

        self._drive.x = self.controller.turn
        self._drive.y = self.controller.forward
        self._drive.label = self.controller.name

        self.draw()
        pygame.display.flip()

    @property
    def velocity(self):
        raise AttributeError("Write only!")

    @velocity.setter
    def velocity(self, value):
        self._velocity.value = abs(value)

    @property
    def rpm_l(self):
        raise AttributeError("Write only!")

    @rpm_l.setter
    def rpm_l(self, value):
        self._rpm_l.value = value

    @property
    def rpm_r(self):
        raise AttributeError("Write only!")

    @rpm_r.setter
    def rpm_r(self, value):
        self._rpm_r.value = value

    @property
    def samples(self):
        raise AttributeError("Write only!")

    @samples.setter
    def samples(self, value):
        self._map.samples = value

    @property
    def load(self):
        raise AttributeError("Write only!")

    @load.setter
    def load(self, value):
        self._load.value = 100 * value

    @property
    def kP(self):
        return self._p_slider.value

    @kP.setter
    def kP(self, value):
        self._p_slider.value = value

    @property
    def kI(self):
        return self._i_slider.value

    @kI.setter
    def kI(self, value):
        self._i_slider.value = value

    @property
    def kD(self):
        return self._d_slider.value

    @kD.setter
    def kD(self, value):
        self._d_slider.value = value

    @property
    def pid_callback(self):
        raise AttributeError("Write only!")

    @pid_callback.setter
    def pid_callback(self, callback):
        self._p_slider.callback = callback
        self._i_slider.callback = callback
        self._d_slider.callback = callback

    @property
    def world_map(self):
        raise AttributeError("Write only!")

    @world_map.setter
    def world_map(self, world_map):
        self._map.polygons = world_map

    @property
    def path(self):
        raise AttributeError("Write only!")

    @path.setter
    def path(self, path):
        self._map.lines = [path]

    @property
    def target():
        raise AttributeError("Write only!")

    @target.setter
    def target(self, state):
        if state is not None:
            self._map.offset = (-state.x, -state.y)
