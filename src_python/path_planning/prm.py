from . import local_planner
from . import path_iterator

import logging
import heapq
import collections
import math
import random

import kdtree

class _Node:
    __slots__ = ("state", "connections", "pf_index", "travel_time", "cost", "previous")

    Connection = collections.namedtuple("Connection", ["node", "travel_time", "cost"])

    def __init__(self, state):
        self.state = state
        self.connections = []
        self.pf_index = -1
        self.previous = None

    def add_connection(self, node, travel_time, cost):
        self.connections.append(self.Connection(node, travel_time, cost))

class Prm:
    """ Probabilistic roadmap """

    min_connection_count = 5
    max_connection_count = 50
    roadmap_nodes = 1000

    def __init__(self, planning_parameters):
        self._parameters = planning_parameters
        self._nodes = kdtree.KdTree()
        self._pf_index = 0

        self._logger = logging.getLogger(__name__)

        self._build_roadmap()

    def plan_path(self, state1, state2):
        node1 = self._add_state(state1)
        if node1 is None:
            raise Exception("Starting position is unreachable")
        node2 = self._add_state(state2)
        if node2 is None:
            raise Exception("Target position is unreachable")

        node_sequence = self._a_star(node1, node2)
        if node_sequence is None:
            return None

        return _PathIterator([node.state for node in node_sequence],
                             node2.travel_time)

    def _a_star(self, start, target):
        def dist_to_target(node):
            path = local_planner.plan_path(node.state, target.state)
            if path is None:
                return math.hypot(node.state.x - target.state.x,
                                  node.state.y - target.state.y)
            else:
                return path.travel_time

        self._pf_index += 1

        waiting = [(dist_to_target(start), start)]
        start.previous = None
        start.travel_time = 0
        start.cost = 0
        start.pf_index = self._pf_index

        while len(waiting):
            _, node = heapq.heappop(waiting)

            if node == target:
                ret = []
                while node is not None:
                    ret.append(node)
                    node = node.previous
                return reversed(ret)

            for child, travel_time, cost in node.connections:
                if child.pf_index == self._pf_index:
                    continue
                child.previous = node
                child.travel_time = node.travel_time + travel_time
                child.cost = node.cost + cost
                child.pf_index = self._pf_index

                heuristic_cost = child.cost + dist_to_target(child)

                heapq.heappush(waiting, (heuristic_cost, child))

        return None

    def _build_roadmap(self):
        random.seed(0)
        for i in range(self.roadmap_nodes):
            if i % 100 == 0:
                self._logger.info("Adding roadmap nodes: %d/%d", i, self.roadmap_nodes)

            node = _Node(self._parameters.random_state())
            if self._parameters.state_cost(node.state) is None:
                continue

            self._nodes.insert((node.state.x, node.state.y), node)

        self._nodes.rebuild()

        count = len(self._nodes)

        for i, (pos, node) in enumerate(self._nodes):
            if i % 100 == 0:
                self._logger.info("Connecting roadmap nodes: %d/%d", i, count)
            self._try_connect(node)

        self._logger.info("Finished building roadmap, %d nodes, %d connections",
                          count, self._get_connection_count())

    def _add_state(self, state):
        cost = self._parameters.state_cost(state)

        if cost is None:
            return None

        node = _Node(state)

        # TODO: Don't add node if it is already in the roadmap

        self._try_connect(node)
        self._nodes.insert((state.x, state.y), node)
        return node

    def _try_connect(self, node):
        attempts = 0
        for _, other in self._nodes.nearest_neighbors((node.state.x, node.state.y)):
            if other is node:
                continue # Don't connect node to itself

            self._try_connect_pair(node, other)
            self._try_connect_pair(other, node)

            attempts += 1

            if len(node.connections) > self.min_connection_count or \
               attempts > self.max_connection_count:
                break

    def _try_connect_pair(self, node1, node2):
        path = local_planner.plan_path(node1.state, node2.state)
        if path is None:
            return False

        travel_time = path.travel_time
        cost = self._path_cost(path)

        if cost is None:
            return False

        node1.add_connection(node2, travel_time, cost)
        return True

    def _path_cost(self, path_iterator, resolution = 0.1):
        """ Estimate integral of self._parameters.state_cost over the states on path_iterator. """

        # TODO: Maybe don't check points one by one, instead try midpoint, quarter points, ....
        # Halton sequence?

        cost = self._parameters.state_cost(path_iterator)
        if cost is None:
            return None

        while True:
            try:
                path_iterator.advance(resolution)
            except StopIteration:
                return cost

            state_cost = self._parameters.state_cost(path_iterator)
            if state_cost is None:
                return None
            else:
                cost += state_cost

    def _get_connection_count(self):
        return sum(len(node[1].connections) for node in self._nodes)

class _PathIterator(path_iterator.PathIterator):
    def __init__(self, states, travel_time):
        if len(states) < 2:
            raise ValueError("There must be at least two states.")
        self._states = states
        self.travel_time = travel_time
        super().__init__()

    def reset(self):
        self.time = 0
        self._i = 0
        self._load_sub()

    def _load_sub(self):
        self._sub = local_planner.plan_path(self._states[self._i],
                                            self._states[self._i + 1])

    def advance(self, dt):
        self.time += dt

        while dt >= self._sub.travel_time - self._sub.time:
            dt -= self._sub.travel_time - self._sub.time
            self._i += 1

            if self._i >= len(self._states) - 1:
                raise StopIteration()

            self._load_sub()

        assert(dt >= 0)
        assert(dt < self._sub.travel_time - self._sub.time)

        if dt == 0:
            return

        self._sub.advance(dt)

    def __getattr__(self, key):
        """ The rest of values gets taken from the sub iterator """
        return getattr(self._sub, key)
