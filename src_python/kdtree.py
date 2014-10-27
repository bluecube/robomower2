import math

class KdTree:
    __slots__ = ("axis", "coord", "left", "right")

    split_threshold = 10

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
        elif len(child) < self.split_threshold:
            child.append((coord, value))
        else:
            new_node = self.__class__()
            new_node.build(child)
            if is_left:
                self.left = new_node
            else:
                self.right = new_node

    def nearest_neighbors(self, coord):
        return (x[1] for x in self._nearest_neighbors(coord))

    def _nearest_neighbors(self, coord):
        is_left = coord[self.axis] < self.coord

        if is_left:
            first_child = self.left
            second_child = self.right
        else:
            first_child = self.right
            second_child = self.left

        distance_to_edge = abs(coord[self.axis] - self.coord)

        first_iterator = self._get_nn_iterator(coord, first_child)
        try:
            first_item = next(first_iterator)

            while first_item[0] < distance_to_edge:
                yield first_item
                first_item = next(first_iterator)

        except StopIteration:
            yield from self._get_nn_iterator(coord, second_child)
            return


        second_iterator = self._get_nn_iterator(coord, second_child)
        try:
            second_item = next(second_iterator)
        except StopIteration:
            yield from first_iterator
            return

        while True:
            if first_item[0] <= second_item[0]:
                yield first_item
                try:
                    first_item = next(first_iterator)
                except StopIteration:
                    yield from second_iterator
                    return
            else:
                yield second_item
                try:
                    second_item = next(second_iterator)
                except StopIteration:
                    yield from second_iterator
                    return

    @classmethod
    def _get_nn_iterator(cls, search_coord, child):
        if isinstance(child, cls):
            return child._nearest_neighbors(search_coord)
        else:
            x = search_coord[0]
            y = search_coord[1]
            return iter(sorted((math.hypot(x - coord[0], y - coord[1]), value)
                                for coord, value
                                in child))

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
