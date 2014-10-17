import .state

class PathIterator:
    @property
    def travel_time(self):
        raise NotImplementedError()



    def reset(self):
        raise NotImplementedError()

    def jump_to(self, time):
        if (time > self.time):
            self.advance(time - self.time)
        else:
            self.reset()
            self.advance(time)

    def advance(self, dt):
        raise NotImplementedError()

    def sample_intervals(self, dt):
        while True:
            yield self.state
            self.advance(dt)



    @property
    def time(self):
        raise NotImplementedError()

    @property
    def x(self):
        raise NotImplementedError()

    @property
    def y(self):
        raise NotImplementedError()

    @property
    def heading(self):
        raise NotImplementedError()

    @property
    def velocity(self):
        raise NotImplementedError()

    @property
    def acceleration(self):
        raise NotImplementedError()

    @property
    def curvature(self):
        raise NotImplementedError()

    @property
    def angular_velocity(self):
        raise NotImplementedError()

    @property
    def state(self):
        return state.State(self.x, self.y,self.heading,
                           self.velocity, self.acceleration,
                           self.curvature)
