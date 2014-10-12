class WorldMap:
    """ This is a map of working area.
    The current implementation is just a placeholder to start testing the path planner,
    later this will probably interface with openstreetmap. """

    def __init__(self):
        self.polygons = [[(5, 5), (10, 5), (10, 10), (5, 10)],
                         [(6, 2), (10, -4), (2, -5)]]

    def has_collision(self, x, y):
        # TODO: The robot is definitely not just a point

        inside = False

        for polygon in self.polygons:
            for i in range(len(polygon)):
                x1, y1 = polygon[i - 1]
                x2, y2 = polygon[i]

                if y2 != y1:
                    t = (y - y1) / (y2 - y1)

                    if t <= 0 or t > 1:
                        continue

                    if x1 + t * (x2 - x1) > x:
                        continue
                else:
                    if y1 != y:
                        continue
                    if min(x1, x2) >= x:
                        continue

                inside = not inside

        return inside
