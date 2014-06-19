import math
import numpy
import itertools

# Based on http://www.cim.mcgill.ca/~stephane/cs507/Project.html
# This implementation only calculate approximation of the Frechet distance, because
# we don't consider all of the poosible critical values of distance (see todo note).

epsilon = 1e-8

def squared_points_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1

    return dx * dx + dy * dy

def _calc_pass(l1, p, distance):
    """Calculate distance along l1 where p is closer than distance."""

    dx = l1[1][0] - l1[0][0]
    dy = l1[1][1] - l1[0][1]

    length_sq = dx * dx + dy * dy

    vx = p[0] - l1[0][0]
    vy = p[1] - l1[0][1]

    a = vx * dx + vy * dy

    D = a * a - length_sq * ((vx * vx + vy * vy) - distance * distance)
    if D < -epsilon:
        return (1, -1)

    if D < 0:
        sqrtD = 0
    else:
        sqrtD = math.sqrt(D)

    return (max((a - sqrtD) / length_sq , 0), min((a + sqrtD) / length_sq, 1))

def _decision(pl1, pl2, distance):
    """Decides if polylines pl1 and pl2 have Frechet distance lower or equal to distance.

    This is the internal version that actually does the work.
    Requires that the start and end points are close enough, but doesn't check this. """

    # Numbers of line segments
    n = len(pl1) - 1
    m = len(pl2) - 1

    b = numpy.empty((2, m + 1))
        # Lowest x coordinate to get into the field i % 2, j from the bottom
        # Value 2 marks that the edge is not passable

    l = numpy.empty((2, m + 1))
        # Lowest y coordinate to get into the field i % 2, j from the left
        # Value 2 marks that the edge is not passable

    for j in range(1, m + 1):
        l[0, j] = 2 # leftmost column is not accessible from the left ...
    l[0, 0] = 0 # ... except for the cell 0, 0.

    # bottommost row is not accessible from the bottom
    b[0, 0] = 2
    b[1, 0] = 2

    for (i, l1) in enumerate(zip(pl1[:-1], pl1[1:])):
        i = i % 2
        ii = 1 - i

        for (j, l2) in enumerate(zip(pl2[:-1], pl2[1:])):
            #print("l[{i}, {j}] = {l}; b[{i}, {j}] = {b}".format(i = i, j = j, l = l[i, j], b = b[i, j]))
            jj = j + 1

            pass_r = _calc_pass(l2, l1[1], distance)
            if b[i, j] <= 1:
                # if the current block could be accessed from the bottom, it can be exited
                # on the right anywhere
                l[ii, j] = pass_r[0]
            else:
                # if it could be accessed only from the left, then find the bottommost
                # possible right exit point
                l[ii, j] = max(pass_r[0], l[i, j])
            if l[ii, j] > pass_r[1] + epsilon:
                # if the best exit point we could find is outside of the passable interval,
                # mark the edge as impassable
                l[ii, j] = 2

            pass_t = _calc_pass(l1, l2[1], distance)
            if l[i, j] <= 1:
                # if the current block could be accessed from the left, it can be exited
                # on the top anywhere, and we do nothing
                b[i, jj] = pass_t[0]
            else:
                # if it could be accessed only from the bottom, then find the leftmost
                # possible top exit point
                b[i, jj] = max(pass_t[0], b[i, j])
            if b[i, jj] > pass_t[1] + epsilon:
                # if the best exit point we could find is outside of the passable interval,
                # mark the edge as impassable
                b[i, jj] = 2

    return b[(n - 1) % 2, m - 1] <= 1 or l[(n - 1) % 2, (m - 1)] <= 1

def _critical_distances_half(pl1, pl2):
    for l in zip(pl1[:-1], pl1[1:]):
        for i, p in enumerate(pl2[1:-1]):
            dx = l[1][0] - l[0][0]
            dy = l[1][1] - l[0][1]
            length = math.hypot(dx, dy)

            # The simple case: Distance between each segment of pl1 and each point of pl2
            yield abs((dy * p[0] - dx * p[1] - l[0][0] * l[1][1] + l[1][0] * l[0][1]) / length)

def _critical_distances(pl1, pl2):
    """ Return candidate values of distance for the actual Frechet distance"""

    yield math.sqrt(squared_points_distance(pl1[0], pl2[0]))
    yield math.sqrt(squared_points_distance(pl1[-1], pl2[-1]))
    yield from _critical_distances_half(pl1, pl2)
    yield from _critical_distances_half(pl2, pl1)

def frechet_distance_decision(pl1, pl2, distance):
    """Decides if polylines pl1 and pl2 have Frechet distance lower or equal to distance."""

    if squared_points_distance(pl1[0], pl2[0]) > distance * distance:
        return False
    if squared_points_distance(pl1[-1], pl2[-1]) > distance * distance:
        return False

    # to decrease memory requirements of the decision version a little bit
    if len(pl1) < len(pl2):
        pl1, pl2 = pl2, pl1

    return _decision(pl1, pl2, distance)

def frechet_distance(pl1, pl2):
    if len(pl1) < len(pl2):
        pl1, pl2 = pl2, pl1

    distances = sorted(_critical_distances(pl1, pl2))
    print(distances)

    assert frechet_distance_decision(pl1, pl2, distances[-1])

    low = 0
    high = len(distances) - 1
    while high > low + 1:
        current = (low + high) // 2
        if _decision(pl1, pl2, distances[current]):
            high = current
        else:
            low = current

    return distances[high]
