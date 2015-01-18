import pygame.joystick
import logging

pygame.joystick.init()

class JoystickController:
    def __init__(self, drive, config):
        self._drive = drive
        self._logger = logging.getLogger(__name__)

        self._max_velocity = config["limits"]["velocity"]
        self.forward = 0

        self._max_angular_velocity = config["limits"]["angular_velocity"]
        self.turn = 0

        self._nonlinearity = config["joystick"]["nonlinearity"]

        if pygame.joystick.get_count() == 0:
            self._joystick = None
            self._logger.info("No joystick found")
        else:
            self._joystick = pygame.joystick.Joystick(0)
            self._joystick.init()
            self._logger.info("Using joystick " + self._joystick.get_name())

    def update(self, delta_t):
        if self._joystick is None:
            self._drive.set_command(0, 0)
            return
        x = -self._joystick.get_axis(2)
        y = -self._joystick.get_axis(1)
        alpha = self._nonlinearity

        self.turn = self._max_angular_velocity * x * (alpha * x * x + 1 - alpha);
        self.forward =      self._max_velocity * y * (alpha * y * y + 1 - alpha);

        self._drive.set_command(self.forward, self.turn)
