import pygame
import logging
from . import config
from . import widgets

pygame.init()

class Gui:
    logger = logging.getLogger(__name__)

    grid_cell_size = 150

    def _set_mode(self, size = (0, 0)):
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)

    def __init__(self):
        self._set_mode()

        self.forward = 0
        self.turn = 0
        self.finished = False

        self.speed = widgets.Dial("fwd velocity", 0, 1.5, "%.1f", "%.2f", "m/s")
        self.battery = widgets.Dial("bat", 0, 100, "%d", "%d", "%")
        self.battery.value = 100
        self.drive = widgets.Xy("drive input")

        self.grid = widgets.Grid(2, [self.speed, self.drive,
                                  self.battery],
                                 5)

        self.logger.info("GUI ready")

    def draw(self):
        w, h = self.screen.get_size()

        self.screen.fill(config.bgcolor)


        grid_width = self.grid.columns * self.grid_cell_size
        self.grid.draw(self.screen, w - grid_width, 0,
                       grid_width, self.grid.rows * self.grid_cell_size)

    def update(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.finished = True
                return
            elif event.type == pygame.VIDEORESIZE:
                self._set_mode(event.size)

        self.drive.x = self.turn
        self.drive.y = self.forward

        self.draw()
        pygame.display.flip()
