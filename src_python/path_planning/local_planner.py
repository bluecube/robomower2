#!/usr/bin/python3

import numpy
import math
try:
    from . import state
except SystemError:
    import state

_interpolation_steps = 20
epsilon = 1e-6

_A = numpy.array([[1, 0, 0, 0,  0,  0], # x(0)
                  [1, 1, 1, 1,  1,  1], # x(1)
                  [0, 1, 0, 0,  0,  0], # diff(x)(0)
                  [0, 1, 2, 3,  4,  5], # diff(x)(1)
                  [0, 0, 2, 0,  0,  0], # diff(diff(x))(0)
                  [0, 0, 2, 6, 12, 20]]) # diff(diff(x))(1)

class _PathIterator:
    # Path properties:

    # self.travel_time
    # self.length

    # Moving through the path:

    def reset(self):
        self.time = 0
        self.distance = 0
        self._curve_param = 0
        self._i = 0
        self._last_interpolation_distance = 0

    def jump_to(self, time):
        self.reset()
        self.advance(time)

    def advance(self, dt):
        self.time += dt

        if self.time > self.travel_time:
            raise StopIteration()

        self.distance = self._iv(self.time)
        remaining_distance = self.distance - self._last_interpolation_distance

        for s in self._interpolation_table[self._i:]:
            if remaining_distance < s:
                self._curve_param = (self._i / _interpolation_steps) + (remaining_distance / (_interpolation_steps * s))
                break
            else:
                remaining_distance -= s
                self._i += 1
                self._last_interpolation_distance += s

    def __iter__(self):
        return self

    def __next__(self):
        self.advance(1e-3)
        return self

    # Accessing current state:

    # self.time
    # self.distance

    @property
    def x(self):
        return self._x(self._curve_param)

    @property
    def y(self):
        return self._y(self._curve_param)

    @property
    def heading(self):
        return math.atan2(self._dy(self._curve_param), self._dx(self._curve_param))

    @property
    def velocity(self):
        return self._v(self.time)

    @property
    def acceleration(self):
        return self._dv(self.time)

    @property
    def curvature(self):
        dx = self._dx(self._curve_param)
        ddx = self._ddx(self._curve_param)
        dy = self._dy(self._curve_param)
        ddy = self._ddy(self._curve_param)
        length = dx * dx + dy * dy
        return (dx * ddy + dy * ddx) / (length**1.5)

    @property
    def angular_velocity(self):
        return self.curvature * self.velocity

    @property
    def state(self):
        return state.State(self.x, self.y,self.heading,
                           self.velocity, self.acceleration,
                           self.curvature)


def plan_path(state1, state2):
    """ Find path from state1 to state2, ignoring obstacles."""

    # Mixing endpoint velocity into the endpoint derivations generates smoother
    # paths (ratios 0.5 and 0.5 were experimentally chosen for the smoothest paths).
    rawdist = math.hypot(state2.x - state1.x, state2.y - state1.y)
    len1 = 0.5 * rawdist + 0.5 * state1.velocity
    len2 = 0.5 * rawdist + 0.5 * state2.velocity

    diff1x = len1 * math.cos(state1.heading)
    diff1y = len1 * math.sin(state1.heading)
    diff2x = len2 * math.cos(state2.heading)
    diff2y = len2 * math.sin(state2.heading)

    b = numpy.array([state1.x,
                     state2.x,
                     diff1x,
                     diff2x,
                     - state1.curvature * len1 * diff1y,
                     - state2.curvature * len2 * diff2y])
    x = numpy.polynomial.Polynomial(numpy.linalg.solve(_A, b))

    b = numpy.array([state1.y,
                     state2.y,
                     diff1y,
                     diff2y,
                     state1.curvature * len1 * diff1x,
                     state2.curvature * len2 * diff2x])
    y = numpy.polynomial.Polynomial(numpy.linalg.solve(_A, b))

    # Array of distances at fixed t values. Used for interpolating curve
    # parameter from distance along the curve
    interpolation_table = []
    length = 0

    prev_x = state1.x
    prev_y = state1.y
    for i in range(1, _interpolation_steps + 1):
        t = i / _interpolation_steps # Curve parameter
        xx = x(t)
        yy = y(t)
        dist = math.hypot(xx - prev_x, yy - prev_y)
        length += dist
        interpolation_table.append(dist)
        prev_x = xx
        prev_y = yy

    assert(len(interpolation_table) == _interpolation_steps)
    #length = scipy.integrate.fixed_quad(lambda p: numpy.sqrt(dx(p) * dx(p) + dy(p) * dy(p)), 0, 1)[0]

    a = state1.acceleration - state2.acceleration
    b = 6 * (state1.velocity + state2.velocity)
    c = -12 * length

    if abs(a) < epsilon:
        travel_time = -c / b
    else:
        D = b * b - 4 * a * c
        if D < 0:
            return None

        travel_time = (- b + math.sqrt(D)) / (2 * a)

        #if travel_time < 0:
        #    travel_time = c / (travel_time * a)

    assert(travel_time > 0)

    b = numpy.array([state1.velocity,
                     state2.velocity,
                     state1.acceleration,
                     state2.acceleration])
    v = numpy.polynomial.Polynomial(numpy.linalg.solve(_A[:4, :4], b),
                                    domain=(0, travel_time),
                                    window=(0, 1))

    it = _PathIterator()
    it.reset()
    it.length = length
    it.travel_time = travel_time
    it._x = x
    it._dx = x.deriv()
    it._ddx = it._dx.deriv()
    it._y = y
    it._dy = y.deriv()
    it._ddy = it._dy.deriv()
    it._v = v
    it._dv = v.deriv()
    it._iv = v.integ()
    it._interpolation_table = interpolation_table

    return it

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    state1 = state.State(0, 0, math.radians(90), 1, 0, -3)
    state2 = state.State(5, 1, math.radians(90), 0, 0, 0)

    iterator = plan_path(state1, state2)

    plot_n = 1000

    t = numpy.empty(plot_n)
    x = numpy.empty(plot_n)
    y = numpy.empty(plot_n)
    v = numpy.empty(plot_n)
    omega = numpy.empty(plot_n)
    for i in range(plot_n):
        t[i] = iterator.time
        x[i] = iterator.x
        y[i] = iterator.y
        v[i] = iterator.velocity
        omega[i] = iterator.angular_velocity
        try:
            iterator.advance(iterator.travel_time / plot_n)
        except StopIteration:
            break

    plt.figure(1)
    plt.subplot(121)
    plt.plot(x, y, "-r", label="Path")
    plt.axis('equal')
    plt.legend()
    plt.subplot(222)
    plt.plot(t, v, "-r", label="Velocity")
    plt.legend()
    plt.subplot(224)
    plt.plot(t, omega, "-r", label="Angular velocity")
    plt.legend()
    plt.show()
