import math

class KdTree:
    __slots__ = ("axis", "coord", "left", "right")

    split_threshold = 2

    def __init__(self):
        self.axis = 0
        self.coord = 0
        self.left = []
        self.right = []

    def insert(self, coord, value):
        is_left = coord[self.axis] < self.coord
        child = is_left and self.left or self.right

        if isinstance(child, self.__class__):
            child.insert(coord, value)
        else:
            child.append((coord, value))

            if len(child) > self.split_threshold:
                new_node = self.__class__()
                new_node.build(child)
                if is_left:
                    self.left = new_node
                else:
                    self.right = new_node

    def nearest_neighbors(self, coord):
        return ((x[1], x[2]) for x in self._nearest_neighbors(self, coord, float("inf")))

    @classmethod
    def _nearest_neighbors(cls, node, coord, distance_to_edge):
        if not isinstance(node, cls):
            yield from sorted((math.hypot(coord[0] - item_coord[0],
                                          coord[1] - item_coord[1]),
                               item_coord, value)
                              for item_coord, value
                              in node)
            return

        is_left = coord[node.axis] < node.coord

        if is_left:
            first_child = node.left
            second_child = node.right
        else:
            first_child = node.right
            second_child = node.left

        distance_to_edge = min(distance_to_edge, abs(coord[node.axis] - node.coord))

        first_iterator = cls._nearest_neighbors(first_child, coord, distance_to_edge)
        try:
            first_item = next(first_iterator)

            while first_item[0] < distance_to_edge:
                yield first_item
                first_item = next(first_iterator)

        except StopIteration:
            yield from cls._nearest_neighbors(second_child, coord, distance_to_edge)
            return

        second_iterator = cls._nearest_neighbors(second_child, coord, distance_to_edge)
        try:
            second_item = next(second_iterator)
        except StopIteration:
            yield first_item
            yield from first_iterator
            return

        while True:
            if first_item[0] <= second_item[0]:
                yield first_item
                try:
                    first_item = next(first_iterator)
                except StopIteration:
                    yield second_item
                    yield from second_iterator
                    return
            else:
                yield second_item
                try:
                    second_item = next(second_iterator)
                except StopIteration:
                    yield first_item
                    yield from first_iterator
                    return

    def build(self, data):
        min_x = float("inf")
        max_x = -float("inf")
        min_y = float("inf")
        max_y = -float("inf")

        for coord, value in data:
            x = coord[0]
            y = coord[1]
            min_x = min(x, min_x)
            max_x = max(x, max_x)
            min_y = min(y, min_y)
            max_y = max(y, max_y)

        self._build(data, min_x, max_x, min_y, max_y)

    def _build(self, data, min_x, max_x, min_y, max_y):
        if max_x - min_x > max_y - min_y:
            self.axis = 0
        else:
            self.axis = 1

        # TODO: Don't sort along the same axis twice
        # TODO: Maybe only approximate median sampling several random nodes.
        sorted_data = sorted(data, key=lambda x: x[0][self.axis])
        split_index = len(data) // 2

        left_data = sorted_data[:split_index]
        right_data = sorted_data[split_index:]

        self.coord = right_data[0][0][self.axis]

        if len(left_data) < self.split_threshold:
            self.left = left_data
        else:
            self.left = self.__class__()
            self.left.build(left_data)

        if len(right_data) < self.split_threshold:
            self.right = right_data
        else:
            self.right = self.__class__()
            self.right.build(right_data)

        # TODO: Reuse the bounding box

    def rebuild(self):
        self.build(self)

    def __len__(self):
        return len(self.left) + len(self.right)

    def __iter__(self):
        yield from self.left
        yield from self.right

    def pprint(self):
        for line in self._pprint_lines():
            print(line)

    def _pprint_lines(self, indent = []):
        yield self._pprint_level_str(indent) + ('x', 'y')[self.axis] + " = " + str(self.coord)

        left_indent = indent + [True]
        if isinstance(self.left, self.__class__):
            yield from self.left._pprint_lines(left_indent)
        else:
            yield self._pprint_level_str(left_indent) + str(self.left)

        right_indent = indent + [False]
        if isinstance(self.right, self.__class__):
            yield from self.right._pprint_lines(right_indent)
        else:
            yield self._pprint_level_str(right_indent) + str(self.right)

    @staticmethod
    def _pprint_level_str(indent):
        level_str = ''.join((level and '| ' or '  ') for level in indent[:-1])

        if len(indent):
            level_str += '|-- '

        return level_str
