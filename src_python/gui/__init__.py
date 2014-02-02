import pygame
import logging
from . import config
from . import widgets
from . import mapwidget

pygame.init()

class KeyboardJoy:
    up = pygame.K_w
    left = pygame.K_a
    down = pygame.K_s
    right = pygame.K_d
    def __init__(self, x_accel, y_accel, nonlinearity):
        self._x = 0
        self._y = 0
        self.a = nonlinearity
        self._x_accel = x_accel
        self._y_accel = y_accel

        if pygame.joystick.get_count() > 0:
            self._use_joystick()
        else:
            self._use_keyboard()


    def update(self, delta_t):
        if self._joystick is not None:
            self._x = self._joystick.get_axis(0)
            self._y = -self._joystick.get_axis(1)
        else:
            pressed = pygame.key.get_pressed()

            if pressed[self.left]:
                if not pressed[self.right]:
                    self._x = max(-1, self._x - self._x_accel * delta_t)
            elif pressed[self.right]:
                self._x = min(1, self._x + self._x_accel * delta_t)
            elif self._x > 0:
                self._x = max(0, self._x - self._x_accel * delta_t)
            elif self._x < 0:
                self._x = min(0, self._x + self._x_accel * delta_t)

            if pressed[self.up]:
                if not pressed[self.down]:
                    self._y = min(1, self._y + self._y_accel * delta_t)
            elif pressed[self.down]:
                self._y = max(-1, self._y - self._y_accel * delta_t)
            elif self._y > 0:
                self._y = max(0, self._y - self._y_accel * delta_t)
            elif self._y < 0:
                self._y = min(0, self._y + self._y_accel * delta_t)

        self.x = self.a * self._x * self._x * self._x + (1 - self.a) * self._x
        self.y = self.a * self._y * self._y * self._y + (1 - self.a) * self._y

    def _use_keyboard(self):
        self._joystick = None
        self.name = "keyboard"

    def _use_joystick(self):
        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()
        self.name = self._joystick.get_name()

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
        self._limits = lim

        self.forward = 0
        self.turn = 0
        self.finished = False

        self.velocity = 0

        self._joystick = KeyboardJoy(lim["angular_acceleration"] / lim["angular_velocity"],
                                    lim["acceleration"] / lim["velocity"],
                                    robot_config["gui"]["joystick_nonlinearity"])

        self._velocity = widgets.Dial("fwd velocity", 0, 1.5, "%.1f", "%.2f", "m/s")
        self._battery = widgets.Dial("bat", 0, 100, "%d", "%d", "%")
        self._battery.value = 100
        self._drive = widgets.Xy(["drive input", ""],
                                 -lim["angular_velocity"],
                                 lim["velocity"],
                                 "%.2f rad/s", "%.2f m/s")
        self._grid = widgets.Grid(self.grid_columns,
                                  [self._velocity, self._drive, self._battery],
                                  5)
        self._map = mapwidget.MapWidget()
        self._map.samples = [(0,0), (5, 10), (16, 7), (10, 10)]

        self.logger.info("GUI ready")

    def draw(self):
        w, h = self.screen.get_size()

        self.screen.fill(config.bgcolor)


        self._grid.draw(self.screen, w - self.grid_width, 0,
                        self.grid_width, self._grid.rows * self.grid_cell_size)
        self._map.draw(self.screen, 0, 0, w - self.grid_width, h)

    def update(self, delta_t):
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

        self._joystick.update(delta_t)

        self.turn = -self._joystick.x * self._limits["angular_velocity"]
        self.forward = self._joystick.y * self._limits["velocity"]

        self._drive.x = self.turn
        self._drive.y = self.forward
        self._drive.label[1] = self._joystick.name

        self._velocity.value = self.velocity

        self.draw()
        pygame.display.flip()
