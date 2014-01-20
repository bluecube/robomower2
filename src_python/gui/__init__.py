import pygame
import logging
from . import config
from . import widgets

pygame.init()

class KeyboardJoy:
    up = pygame.K_w
    left = pygame.K_a
    down = pygame.K_s
    right = pygame.K_d
    def __init__(self, x_accel, y_accel):
        self.x = 0
        self.y = 0
        self._x_accel = x_accel
        self._y_accel = y_accel

    def update(self, delta_t):
        pressed = pygame.key.get_pressed()

        if pressed[self.left]:
            if not pressed[self.right]:
                self.x = max(-1, self.x - self._x_accel * delta_t)
        elif pressed[self.right]:
            self.x = min(1, self.x + self._x_accel * delta_t)
        elif self.x > 0:
            self.x = max(0, self.x - self._x_accel * delta_t)
        elif self.x < 0:
            self.x = min(0, self.x + self._x_accel * delta_t)

        if pressed[self.up]:
            if not pressed[self.down]:
                self.y = max(-1, self.y - self._y_accel * delta_t)
        elif pressed[self.down]:
            self.y = min(1, self.y + self._y_accel * delta_t)
        elif self.y > 0:
            self.y = max(0, self.y - self._y_accel * delta_t)
        elif self.y < 0:
            self.y = min(0, self.y + self._y_accel * delta_t)

class Gui:
    logger = logging.getLogger(__name__)

    grid_cell_size = 150

    def _set_mode(self, size = (0, 0)):
        self.screen = pygame.display.set_mode(size, pygame.RESIZABLE)

    def __init__(self, robot_config):
        self._set_mode()

        self.robot_config = robot_config

        self.forward = 0
        self.turn = 0
        self.finished = False

        self.keyboard = KeyboardJoy(robot_config["dimensions"]["max_angular_acceleration"],
                                    robot_config["dimensions"]["max_acceleration"])

        self.speed = widgets.Dial("fwd velocity", 0, 1.5, "%.1f", "%.2f", "m/s")
        self.battery = widgets.Dial("bat", 0, 100, "%d", "%d", "%")
        self.battery.value = 100
        self.drive = widgets.Xy(["drive input", "keyboard"],
                                robot_config["dimensions"]["max_angular_velocity"],
                                robot_config["dimensions"]["max_velocity"],
                                "%.2f rad/s", "%.2f m/s")

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

    def update(self, delta_t):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.finished = True
                return
            elif event.type == pygame.VIDEORESIZE:
                self._set_mode(event.size)

        self.keyboard.update(delta_t)

        self.turn = self.keyboard.x * self.robot_config["dimensions"]["max_angular_velocity"]
        self.forward = self.keyboard.y * self.robot_config["dimensions"]["max_velocity"]

        self.drive.x = self.turn
        self.drive.y = self.forward

        self.draw()
        pygame.display.flip()
