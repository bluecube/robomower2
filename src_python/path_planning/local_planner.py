#!/usr/bin/python3

import numpy
import math
from . import state
from . import path_iterator

_interpolation_steps = 200
epsilon = 1e-6

_A = numpy.array([[1, 0, 0, 0,  0,  0], # x(0)
                  [1, 1, 1, 1,  1,  1], # x(1)
                  [0, 1, 0, 0,  0,  0], # diff(x)(0)
                  [0, 1, 2, 3,  4,  5], # diff(x)(1)
                  [0, 0, 2, 0,  0,  0], # diff(diff(x))(0)
                  [0, 0, 2, 6, 12, 20]]) # diff(diff(x))(1)

class _PathIterator(path_iterator.PathIterator):
    # Path properties:

    # self.travel_time

    # Moving through the path:

    def reset(self):
        self.time = 0
        self._curve_param = 0
        self._i = 0
        self._last_interpolation_distance = 0

    def advance(self, dt):
        self.time += dt

        if self.time > self.travel_time:
            self.time = self.travel_time
            self._curve_param = 1
            self._i = len(self._interpolation_table)
            return

        remaining_distance = self._iv(self.time) - self._last_interpolation_distance

        self._curve_param = 1 # This value is used when self.time == self.travel_time
        for s in self._interpolation_table[self._i:]:
            if remaining_distance < s:
                self._curve_param = (self._i / _interpolation_steps) + (remaining_distance / (_interpolation_steps * s))
                break
            else:
                remaining_distance -= s
                self._i += 1
                self._last_interpolation_distance += s

    def finished(self):
        return self.time >= self.travel_time

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
    def jerk(self):
        return self._ddv(self.time)

    @property
    def curvature(self):
        dx = self._dx(self._curve_param)
        ddx = self._ddx(self._curve_param)
        dy = self._dy(self._curve_param)
        ddy = self._ddy(self._curve_param)
        length = dx * dx + dy * dy
        return (dx * ddy - dy * ddx) / (length**1.5)


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
        if abs(b) < epsilon:
            return None
        travel_time = -c / b
    else:
        D = b * b - 4 * a * c
        if D < 0:
            return None

        travel_time = (- b + math.sqrt(D)) / (2 * a)

        #if travel_time < 0:
        #    travel_time = c / (travel_time * a)

    assert(travel_time > 0)

    t = travel_time
    t2 = t * t
    t3 = t * t2
    A = numpy.array([[1, 0,      0,       0], # v(0)
                     [1, t,     t2,      t3], # v(1)
                     [0, 1,      0,       0], # diff(v)(0)
                     [0, 1,  2 * t,  3 * t2]]) # diff(v)(1)
    b = numpy.array([state1.velocity,
                     state2.velocity,
                     state1.acceleration,
                     state2.acceleration])
    v = numpy.polynomial.Polynomial(numpy.linalg.solve(A, b));

    it = _PathIterator()
    it.reset()
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
