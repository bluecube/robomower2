#!/usr/bin/python3

import numpy
import math
try:
    from . import state
except SystemError:
    import state


v_max = 2
at_max = 1
ar_max = 2
j_max = 10
omega_max = 1

interpolation_steps = 20
epsilon = 1e-6

_A = numpy.array([[1, 0, 0, 0,  0,  0], # x(0)
                  [1, 1, 1, 1,  1,  1], # x(1)
                  [0, 1, 0, 0,  0,  0], # diff(x)(0)
                  [0, 1, 2, 3,  4,  5], # diff(x)(1)
                  [0, 0, 2, 0,  0,  0], # diff(diff(x))(0)
                  [0, 0, 2, 6, 12, 20]]) # diff(diff(x))(1)

def _check_poly_positive(p, maximum):
    """ Check if p(t) > 0 for all t in [0, 1] """
    if p(0) < -epsilon or p(maximum) < -epsilon:
        return False

    for t in p.deriv().roots():
        if t < 0 or t > maximum:
            continue
        if p(t) < -epsilon:
            return False

    return True

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
    for i in range(1, interpolation_steps + 1):
        t = i / interpolation_steps # Curve parameter
        xx = x(t)
        yy = y(t)
        dist = math.hypot(xx - prev_x, yy - prev_y)
        length += dist
        interpolation_table.append(dist)
        prev_x = xx
        prev_y = yy

    assert(len(interpolation_table) == interpolation_steps)
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

    assert(_check_poly_positive(v, travel_time)) # This should be true because D is positive ... really?

    dx = x.deriv()
    dy = y.deriv()
    dv = v.deriv()
    ddx = dx.deriv()
    ddy = dy.deriv()
    ddv = dv.deriv()
    iv = v.integ()

    # Verify dynamic properties not depending on curvature.
    # These are verified exactly (for the whole curve at once).
    if not _check_poly_positive(v_max - v, travel_time):
        print("Velocity limit exceeded")
        return None

    if not _check_poly_positive(at_max - dv, travel_time) or \
       not _check_poly_positive(at_max + dv, travel_time):
        print("Velocity limit exceeded")
        return None

    if not _check_poly_positive(j_max - ddv, travel_time) or \
       not _check_poly_positive(j_max + ddv, travel_time):
        print("Jerk limit exceeded")
        return None

    def ret(time):
        # interpolate the curve parameter:
        t = 1
        remaining_distance = iv(time)
        for i, s in enumerate(interpolation_table):
            if remaining_distance < s:
                t = (i / interpolation_steps) + (remaining_distance / (interpolation_steps * s))
                break
            else:
                remaining_distance -= s

        dxx = dx(t)
        dyy = dy(t)
        ddxx = ddx(t)
        ddyy = ddy(t)

        factor = math.hypot(dxx, dyy)
        curvature = (dxx * ddyy - dyy * ddxx) / (factor * factor * factor)

        vv = v(time)
        omega = curvature * vv

        return x(t), y(t), vv, omega, dv(time)

    return travel_time, ret # TODO: Return path iterator instead of this

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    state1 = state.State(0, 0, math.radians(90), 1, 0, -3)
    state2 = state.State(5, 1, math.radians(90), 0, 0, 0)

    travel_time, func = plan_path(state1, state2)

    t = numpy.linspace(0, travel_time, 1000)
    x, y, v, omega, at = zip(*[func(x) for x in t])

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
