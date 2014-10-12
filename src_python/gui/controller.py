import pygame

class GuiController:
    up = pygame.K_w
    left = pygame.K_a
    down = pygame.K_s
    right = pygame.K_d

    def __init__(self, gui):
        lim = gui._config["limits"]

        self._max_velocity = lim["velocity"]
        self._x_accel = 0.25 / lim["angular_velocity"]
        self._x = 0
        self.forward = 0

        self._max_angular_velocity = lim["angular_velocity"]
        self._y_accel = lim["acceleration"] / lim["velocity"]
        self._y = 0
        self.turn = 0

        self._nonlinearity = gui._config["gui"]["joystick_nonlinearity"]

        if pygame.joystick.get_count() > 0:
            self._use_joystick()
        else:
            self._use_keyboard()

    def update(self, delta_t):
        if self._joystick is not None:
            self._x = -self._joystick.get_axis(2)
            self._y = -self._joystick.get_axis(1)
        else:
            pressed = pygame.key.get_pressed()

            if pressed[self.right]:
                if not pressed[self.left]:
                    self._x = max(-1, self._x - self._x_accel * delta_t)
            elif pressed[self.left]:
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

        self.turn = self._max_angular_velocity * self._x * (self._nonlinearity * self._x * self._x +
                                                            1 - self._nonlinearity);
        self.forward = self._max_velocity * self._y * (self._nonlinearity * self._y * self._y +
                                                       1 - self._nonlinearity);

    def _use_keyboard(self):
        self._joystick = None
        self.name = "keyboard"

    def _use_joystick(self):
        self._joystick = pygame.joystick.Joystick(0)
        self._joystick.init()
        self.name = self._joystick.get_name()

