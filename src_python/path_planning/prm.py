from . import local_planner
from . import path_iterator

import logging
import heapq
import collections
import math
import random
import itertools

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

    max_neighbors = 10
    neighbors_examined = 5 * max_neighbors
    maxdist = 10
    roadmap_nodes = 200
    smoothing_tries = 20

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

        node_sequence = self._path_smoothing(list(node_sequence))

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
        for i in range(self.roadmap_nodes):
            if i % 50 == 0:
                self._logger.info("Adding roadmap nodes: %d/%d", i, self.roadmap_nodes)
            self._add_state(self._parameters.random_state())

        self._nodes.rebuild()

        self._logger.info("Finished building roadmap, %d nodes, %d connections",
                          len(self._nodes), self._get_connection_count())

    def _add_state(self, state):
        cost = self._parameters.state_cost(state)

        if cost is None:
            return None

        node = _Node(state)

        # TODO: Don't add node if it is already in the roadmap

        forward_neighbors = []
        backward_neighbors = []

        for _, neighbor in itertools.islice(self._nodes.nearest_neighbors((state.x, state.y)),
                                         self.neighbors_examined):
            path = local_planner.plan_path(state, neighbor.state)
            if path is not None and path.travel_time < self.maxdist:
                forward_neighbors.append((path.travel_time, neighbor))

            path = local_planner.plan_path(neighbor.state, state)
            if path is not None and path.travel_time < self.maxdist:
                backward_neighbors.append((path.travel_time, neighbor))

        forward_neighbors.sort()
        backward_neighbors.sort()

        for distance, neighbor in forward_neighbors[:self.max_neighbors]:
            self._maybe_connect(node, neighbor)

        for distance, neighbor in backward_neighbors[:self.max_neighbors]:
            self._maybe_connect(neighbor, node)

        self._nodes.insert((state.x, state.y), node)
        return node

    def _maybe_connect(self, node1, node2):
        #if self._a_star(node1, node2) is not None:
        #    # If there is already a path, we don't need to add another edge
        #    return

        path = local_planner.plan_path(node1.state, node2.state)
        assert path is not None

        cost = self._path_cost(path)
        if cost is None:
            return

        node1.add_connection(node2, path.travel_time, cost)

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

    def _path_smoothing(self, node_sequence):
        costs = []
        print(len(node_sequence))
        for i, (node1, node2) in enumerate(zip(node_sequence[:-1], node_sequence[1:])):
            for connection in node1.connections:
                if connection.node == node2:
                    costs.append(connection.cost)
                    break
            print(len(costs))
            assert len(costs) == i + 1
        assert len(costs) == len(node_sequence) - 1

        for i in range(self.smoothing_tries):
            k = random.randrange(len(node_sequence))
            l = random.randrange(len(node_sequence))
            if k == l:
                continue

            node1 = node_sequence[k]
            node2 = node_sequence[l]

            path = local_planner.plan_path(node1.state, node2.state)
            if path is None:
                continue
            cost = self._path_cost(path)
            if cost is None:
                continue

            if cost >= sum(costs[k:l+1]):
                continue

            # Now we have a local path that is shorter than what the planner found
            # Replace it

            node_sequence = node_sequence[:k + 1] + node_sequence[l:]
            costs = costs[:k] + [cost] + costs[l:]
            assert len(costs) == len(node_sequence) - 1
        return node_sequence


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
