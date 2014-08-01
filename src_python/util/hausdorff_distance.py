import math

def _point_to_point(p1, p2):
    x1, y1 = p1
    x2, y2 = p2

    dx = x2 - x1
    dy = y2 - y1
    return dx * dx + dy * dy

def _point_to_line(p, l):
    x, y = p
    (x1, y1), (x2, y2) = l

    dx = x2 - x1
    dy = y2 - y1

    a = _point_to_point(p, l[0])
    b = _point_to_point(p, l[1])
    c = dx * dx + dy * dy

    if b >= a + c:
        return a
    elif a >= b + c:
        return b
    else:
        tmp = (dy * x - dx * y - x1 * y2 + x2 * y1)
        return tmp * tmp / c

def _point_to_polyline(p, pl):
    return min(_point_to_line(p, l) for l in zip(pl[1:], pl[:-1]))

def squared_oriented_hausdorff_distance(pl1, pl2):
    """ Squared oriented distance between two polylines. """
    return max(_point_to_polyline(p, pl2) for p in pl1)

def squared_hausdorff_distance(pl1, pl2):
    return max(squared_oriented_hausdorff_distance(pl1, pl2),
               squared_oriented_hausdorff_distance(pl2, pl1))

def hausdorff_distance(pl1, pl2):
    return math.sqrt(squared_hausdorff_distance(pl1, pl2))

def average_distance(pl1, pl2):
    """ Something like hausdorff distance between two polylines,
    only instead of maximal error we use average error. """
    avg = 0
    t = 1
    for p in pl1:
        avg += (math.sqrt(_point_to_polyline(p, pl2)) - avg) / t
        t += 1
    for p in pl2:
        avg += (math.sqrt(_point_to_polyline(p, pl1)) - avg) / t
        t += 1
    return avg
