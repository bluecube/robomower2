import math
import numpy
import itertools

# Based on http://www.cim.mcgill.ca/~stephane/cs507/Project.html

def squared_points_distance(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1

    return dx * dx + dy * dy

def _calc_pass(l1, p, epsilon):
    """Calculate distance along l1 where p is closer than epsilon."""

    dx = l1[1][0] - l1[0][0]
    dy = l1[1][1] - l1[0][1]

    length_sq = dx * dx + dy * dy

    vx = p[0] - l1[0][0]
    vy = p[1] - l1[0][1]

    a = vx * dx + vy * dy

    D = a * a - length_sq * ((vx * vx + vy * vy) - epsilon * epsilon)
    if D < 0:
        return (1, -1)
    sqrtD = math.sqrt(D)

    return (max((a - sqrtD) / length_sq , 0), min((a + sqrtD) / length_sq, 1))

def _decision(pl1, pl2, epsilon):
    """Decides if polylines pl1 and pl2 have Frechet distance lower or equal to epsilon.

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

            pass_r = _calc_pass(l2, l1[1], epsilon)
            if b[i, j] <= 1:
                # if the current block could be accessed from the bottom, it can be exited
                # on the right anywhere
                l[ii, j] = pass_r[0]
            else:
                # if it could be accessed only from the left, then find the bottommost
                # possible right exit point
                l[ii, j] = max(pass_r[0], l[i, j])
            if l[ii, j] > pass_r[1]:
                # if the best exit point we could find is outside of the passable interval,
                # mark the edge as impassable
                l[ii, j] = 2

            pass_t = _calc_pass(l1, l2[1], epsilon)
            if l[i, j] <= 1:
                # if the current block could be accessed from the left, it can be exited
                # on the top anywhere, and we do nothing
                b[i, jj] = pass_t[0]
            else:
                # if it could be accessed only from the bottom, then find the leftmost
                # possible top exit point
                b[i, jj] = max(pass_t[0], b[i, j])
            if b[i, jj] > pass_t[1]:
                # if the best exit point we could find is outside of the passable interval,
                # mark the edge as impassable
                b[i, jj] = 2

    return b[(n - 1) % 2, m - 1] <= 1 or l[(n - 1) % 2, (m - 1)] <= 1

def critical_epsilons(pl1, pl2):
    min_epsilon = math.sqrt(max(squared_points_distance(pl1[0], pl2[0]),
                                squared_points_distance(pl1[-1], pl2[-1])))

    yield min_epsilon

    segments1 = list(zip(pl1[:-1], pl1[1:]))
    segments2 = list(zip(pl2[:-1], pl2[1:]))

    for l1 in segments1:
        for l2 in segments2:
            pass

def frechet_distance_decision(pl1, pl2, epsilon):
    """Decides if polylines pl1 and pl2 have Frechet distance lower or equal to epsilon."""

    if squared_points_distance(pl1[0], pl2[0]) > epsilon * epsilon:
        return False
    if squared_points_distance(pl1[-1], pl2[-1]) > epsilon * epsilon:
        return False

    # to decrease memory requirements of the decision version a little bit
    if len(pl1) < len(pl2):
        pl1, pl2 = pl2, pl1

    return _decision(pl1, pl2, epsilon)

def frechet_distance(pl1, pl2):
    # to decrease memory requirements of the decision version a little bit
    if len(pl1) < len(pl2):
        pl1, pl2 = pl2, pl1

    epsilons = sorted(critical_epsilons(pl1, pl2))

    assert frechet_distance_decision(pl1, pl2, epsilons[-1])

    low = 0
    high = len(epsilons - 1)
    while high > low + 1:
        current = (low + high) // 2
        if frechet_distance_decision(pl1, pl2, epsilons[current]):
            high = current
        else:
            low = current

    return epsilons[high]
