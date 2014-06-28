import math
import copy
import random
import logging

class DifferentialDriveModel:
    """ Model for arbitrary differential drive.
    Handles conversions from left/right ticks to velicities and turn rates."""

    def __init__(self,
                 left_resolution, right_resolution,
                 left_sigma, right_sigma,
                 wheel_base):
        self.left_resolution = left_resolution
        self.right_resolution = right_resolution
        self.left_sigma = left_sigma
        self.right_sigma = right_sigma
        self.wheel_base = wheel_base

    def update_sample(self, sample, left_ticks, right_ticks):
        """ Returns a new sample updated according to measured movement."""

        left_distance = left_ticks * self.left_resolution * random.gauss(1, self.left_sigma)
        right_distance = right_ticks * self.right_resolution * random.gauss(1, self.right_sigma)

        forward = (left_distance + right_distance) * 0.5
        turn = (right_distance - left_distance) / self.wheel_base

        alpha = sample.heading + turn / 2

        # For circular paths, shifts of the sample should be multiplied
        # by forward * 2 * math.sin(turn / 2) / turn instead of just forward
        # However for our turn and update rates, we won't be seing turn larger
        # than 0.1 => error is about 0.04%
        #assert abs(turn) < 0.15 # this is not true in the calibration

        sample = copy.copy(sample)

        sample.x += math.cos(alpha) * forward
        sample.y += math.sin(alpha) * forward

        sample.heading += turn

        return sample

    def update_sample_iter(self, sample, ticks):
        yield sample
        for left_ticks, right_ticks in ticks:
            sample = self.update_sample(sample, left_ticks, right_ticks);
            yield sample

    def velocity_to_ticks(self, forward, turn):
        """ Return left and right motor speed in ticks/s to achieve the
        give forward and turn velocity. """

        turn_speed = turn * self.wheel_base / 2
        left_command = (forward - turn_speed) / self.left_resolution
        right_command = (forward + turn_speed) / self.right_resolution

        return (left_command, right_command)

class DifferentialDrive:
    """ Left is positive """
    def __init__(self, left_proxy, right_proxy, config):
        self._logger = logging.getLogger(__name__)

        self.left_proxy = left_proxy
        self.right_proxy = right_proxy
        assert(left_proxy.PID_FREQUENCY == right_proxy.PID_FREQUENCY)

        self.model = DifferentialDriveModel(config["left_resolution"],
                                            config["right_resolution"],
                                            config["left_sigma"],
                                            config["right_sigma"],
                                            config["wheel_base"])
        self.set_pid(**config["PID"])

    def set_pid(self, kP, kI, kD):
        self._logger.info("Setting PID params to %f %f %f", kP, kI, kD)
        self.left_proxy.params(kP, kI, kD)
        self.right_proxy.params(kP, kI, kD)

    def update(self, forward, turn):
        left_command, right_command = self.model.velocity_to_ticks(forward, turn)

        self.left_command = int(left_command / self.left_proxy.PID_FREQUENCY)
        self.right_command = int(right_command / self.right_proxy.PID_FREQUENCY)

        self.left_ticks = self.left_proxy.update(self.left_command)['distance']
        self.right_ticks = self.right_proxy.update(self.right_command)['distance']

    def update_sample(self, sample):
        return self.model.update_sample(sample, self.left_ticks, self.right_ticks)
