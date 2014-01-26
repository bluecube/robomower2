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

        left_proxy.params(config["drive"]["PID"]["kP"],
                          config["drive"]["PID"]["kI"],
                          config["drive"]["PID"]["kD"])
        right_proxy.params(config["drive"]["PID"]["kP"],
                           config["drive"]["PID"]["kI"],
                           config["drive"]["PID"]["kD"])

    def update(self, forward, turn):
        turn_speed = turn * self.wheel_base / 2
        left = forward - turn_speed
        right = forward + turn_speed

        left /= self.velocity_resolution
        right /= self.velocity_resolution

        left_distance = self.left_proxy.update(left)['distance']
        right_distance = self.right_proxy.update(right)['distance']

        self.left_distance = left_distance * self.resolution
        self.right_distance = right_distance * self.resolution

    @property
    def forward_distance(self):
        return (self.left_distance + self.right_distance) / 2

    @property
    def turn_angle(self):
        return (self.right_distance - self.left_distance) / self.wheel_base
