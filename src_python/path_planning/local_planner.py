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

def _find_poly(maximum, value0, value1, deriv0, deriv1):
    """ Return a polynomial p, so that
    p(0) = value0,
    p(maximum) = value1,
    diff(p)(0) = deriv0
    diff(p)(maximum) = deriv1"""

    A = numpy.array([[1, 0, 0, 0], # p(0)
                     [1, 1 * maximum, 1 * maximum * maximum, 1 * maximum * maximum * maximum], # p(1)
                     [0, 1, 0, 0], # diff(p)(0)
                     [0, 1, 2 * maximum, 3 * maximum * maximum]]) # diff(p)(1)
    b = numpy.array([value0,
                     value1,
                     deriv0,
                     deriv1])

    x = numpy.linalg.solve(A, b)
    return numpy.polynomial.Polynomial(x)

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
    # paths (although the derivations are never used directly).
    # We are using average with eucleidean distance between the end points, because
    # otherwise the conditions degenerate with zero end speeds (hello, cpt Obvious).
    # TODO Check this again
    rawdist = math.hypot(state2.x - state1.x, state2.y - state1.y)
    xy_len1 = (rawdist + state1.velocity) / 2
    xy_len2 = (rawdist + state2.velocity) / 2

    x = _find_poly(1,
                   state1.x, state2.x,
                   math.cos(state1.heading) * xy_len1,
                   math.cos(state2.heading) * xy_len1)
    y = _find_poly(1,
                   state1.y, state2.y,
                   math.sin(state1.heading) * xy_len2,
                   math.sin(state2.heading) * xy_len2)

    global x_poly
    global y_poly
    x_poly = x
    y_poly = y


    length = 0
    interpolation_table = [] # Array of distances at fixed t values. Used for interpolating curve
                             # parameter from distance along the curve
    prev_x = state1.x
    prev_y = state1.y
    for i in range(1, interpolation_steps + 1):
        t = i / interpolation_steps # Curve parameter
        xx = x(t)
        yy = x(t)
        dist = math.hypot(xx - prev_x, yy - prev_y)
        length += dist
        interpolation_table.append(dist)
        prev_x = xx
        prev_y = yy

    assert(len(interpolation_table) == interpolation_steps)
    print("length:", length)

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

    v = _find_poly(travel_time,
                   state1.velocity, state2.velocity,
                   state1.acceleration, state2.acceleration)

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

    # Verify dynamic properties depending on curvature.
    # These are verified only approximately, by sampling the values in several points.
    for i in range(interpolation_steps):
        xx, yy, vv, omega, at = ret(travel_time * i / interpolation_steps)

        if abs(omega) > omega_max:
            print("Angular velocity limit exceeded")
            return None

        ar = vv * omega
        if (at / at_max)**2 + (ar / ar_max)**2 > 1:
            print("Acceleration limit exceeded")
            return None

    return travel_time, ret # TODO: Return path iterator instead of this

if __name__ == "__main__":
    import matplotlib.pyplot as plt

    state1 = state.State(0, 0, math.radians(0), 1, 0)
    state2 = state.State(5, 1, math.radians(0), 1, 0.1)
#    state3 = state.State(10, 0, math.radians(0), 1, 0)

    travel_time, func = plan_path(state1, state2)

    t = numpy.linspace(0, travel_time, 1000)
    x, y, v, curvature, at = zip(*[func(x) for x in t])

    plt.figure(1)
    plt.subplot(121)
    plt.plot(x, y, "-r", label="Path")
    plt.axis('equal')
    plt.legend()
    plt.subplot(222)
    plt.plot(t, v, "-r", label="Velocity")
    plt.legend()
    plt.subplot(224)
    plt.plot(t, curvature, "-r", label="Angular velocity")
    plt.show()
