import math

class DifferentialDrive:
    """ Left is positive """
    def __init__(self, left_proxy, right_proxy, config):
        self.left_proxy = left_proxy
        self.right_proxy = right_proxy
        self.wheel_base = config["drive"]["wheel_base"]
        self.resolution = config["drive"]["resolution"]

        # status of the last update
        self.left_distance = None
        self.right_distance = None

        self.velocity_resolution = self.resolution * left_proxy.PID_FREQUENCY
        assert(left_proxy.PID_FREQUENCY == right_proxy.PID_FREQUENCY)

        self.set_pid(**config["drive"]["PID"])

    def set_pid(self, kP, kI, kD):
        self.left_proxy.params(kP, kI, kD)
        self.right_proxy.params(kP, kI, kD)

    def update(self, forward, turn):
        turn_speed = turn * self.wheel_base / 2
        self.left_command = int((forward - turn_speed) / self.velocity_resolution)
        self.right_command = int((forward + turn_speed) / self.velocity_resolution)

        self.left_ticks = self.left_proxy.update(self.left_command)['distance']
        self.right_ticks = self.right_proxy.update(self.right_command)['distance']

    def modify_sample(self, sample):
        forward = self.forward_distance
        turn = self.turn_angle

        alpha = sample.heading + turn / 2

        # For circular paths, shifts of the sample should be multiplied
        # by forward * 2 * math.sin(turn / 2) / turn instead of just forward
        # However for our turn and update rates, we won't be seing turn larger
        # than 0.1 => error is about 0.04%
        assert abs(turn) < 0.15

        sample.x += math.cos(alpha) * forward
        sample.y += math.sin(alpha) * forward

        sample.heading += turn

    @property
    def forward_distance(self):
        return self.resolution * (self.left_ticks + self.right_ticks) / 2

    @property
    def turn_angle(self):
        return self.resolution * (self.right_ticks - self.left_ticks) / self.wheel_base
