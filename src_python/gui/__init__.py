import pygame
import logging
from . import config
from . import widgets
from . import mapwidget
from . import controller

pygame.init()

class Gui:
    logger = logging.getLogger(__name__)

    grid_cell_size = 150
    grid_columns = 2
    grid_width = grid_columns * grid_cell_size

    def _set_mode(self, size = (0, 0)):
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)

    def __init__(self, robot_config):
        self._set_mode()

        lim = robot_config["limits"]
        self._config = robot_config

        self.finished = False

        self.controller = controller.GuiController(self);

        self._velocity = widgets.Dial("velocity", 0, lim["velocity"], "%.1f", "%.2f", "m/s")
        self._drive = widgets.Xy("",
                                 -lim["angular_velocity"],
                                 lim["velocity"],
                                 "%.2f rad/s", "%.2f m/s")
        self._grid = widgets.Grid(self.grid_columns,
                                  [self._velocity, self._drive],
                                  5)
        self._map = mapwidget.MapWidget(robot_config["gui"]["map_zoom"])

        self.logger.info("GUI ready")

    def draw(self):
        w, h = self.screen.get_size()

        self.screen.fill(config.bgcolor)


        self._grid.draw(self.screen, w - self.grid_width, 0,
                        self.grid_width, self._grid.rows * self.grid_cell_size)
        self._map.draw(self.screen, 0, 0, w - self.grid_width, h)

    def update(self):
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

        self._drive.x = self.controller.turn
        self._drive.y = self.controller.forward
        self._drive.label = self.controller.name

        self.draw()
        pygame.display.flip()

    @property
    def velocity(self):
        return self._velocity.value

    @velocity.setter
    def velocity(self, value):
        self._velocity.value = abs(value)

    @property
    def samples(self):
        return self._map.samples

    @samples.setter
    def samples(self, value):
        self._map.samples = value
