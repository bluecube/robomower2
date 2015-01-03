from . import local_planner
from . import path_iterator
from . import state

import logging
import heapq
import collections
import math
import random
import itertools
import os.path
import sys
import gzip
import struct

import kdtree

_Connection = collections.namedtuple("_Connection", ["node", "cost"])

class _Node:
    __slots__ = ("state", "connections", "index", "cost", "previous")

    def __init__(self, state):
        self.state = state
        self.connections = []
        self.index = -1 # Index is a helper field used during path finding and serialization
        self.previous = None

    def add_connection(self, node, cost):
        self.connections.append(_Connection(node, cost))

class Prm:
    """ Probabilistic roadmap """

    max_neighbors = 50
    neighbors_examined = 5 * max_neighbors
    roadmap_nodes = 500
    distance_epsilon = 0.1

    _count_struct = struct.Struct("I")
    _state_struct = struct.Struct("ffffff")
    _connection_struct = struct.Struct("If")

    def __init__(self, planning_parameters):
        self._parameters = planning_parameters
        self._pf_index = 0

        self._logger = logging.getLogger(__name__)

        self._obtain_roadmap()

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

        return _PathIterator([node.state for node in node_sequence])

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
        start.cost = 0
        start.index = self._pf_index

        while len(waiting):
            _, node = heapq.heappop(waiting)

            if node == target:
                ret = []
                while node is not None:
                    ret.append(node)
                    node = node.previous
                return reversed(ret)

            for child, cost in node.connections:
                if child.index == self._pf_index:
                    continue
                child.previous = node
                child.cost = node.cost + cost
                child.index = self._pf_index

                heuristic_cost = child.cost + dist_to_target(child)

                heapq.heappush(waiting, (heuristic_cost, child))

        return None


    def _obtain_roadmap(self):
        roadmap_file = os.path.join(os.path.dirname(sys.argv[0]), "roadmap.gz")

        self._roadmap = kdtree.KdTree()

        try:
            self._logger.info("Loading roadmap from file %s", roadmap_file)
            self._load_roadmap(roadmap_file)
        except FileNotFoundError:
            self._logger.info("Loading roadmap failed, rebuilding")
            self._build_roadmap()
            self._logger.info("Saving roadmap to file %s", roadmap_file)
            self._save_roadmap(roadmap_file)

        self._roadmap.rebuild()
        self._logger.info("Have roadmap with %d nodes and %d connections",
                          len(self._roadmap), self._get_connection_count())

    def _load_roadmap(self, roadmap_file):
        with gzip.open(roadmap_file, "rb") as fp:
            nodes = []
            count = self._count_struct.unpack(fp.read(self._count_struct.size))[0]
            for i in range(count):
                node = _Node(state.State(*self._state_struct.unpack(fp.read(self._state_struct.size))))
                nodes.append(node)
                self._roadmap.insert((node.state.x, node.state.y), node)

            for node in nodes:
                count = self._count_struct.unpack(fp.read(self._count_struct.size))[0]
                for i in range(count):
                    index, cost = self._connection_struct.unpack(fp.read(self._connection_struct.size))
                    node.add_connection(nodes[index], cost)


    def _save_roadmap(self, roadmap_file):
        # Pickle was running into problems with recursion depth, so we serialize it manually
        with gzip.open(roadmap_file, "wb") as fp:
            fp.write(self._count_struct.pack(len(self._roadmap)))
            for i, (_, node) in enumerate(self._roadmap):
                node.index = i
                fp.write(self._state_struct.pack(*node.state))

            for _, node in self._roadmap:
                fp.write(self._count_struct.pack(len(node.connections)))
                for connection in node.connections:
                    fp.write(self._connection_struct.pack(connection.node.index,
                                                          connection.cost))

            for _, node in self._roadmap:
                node.index = -1

    def _build_roadmap(self):
        for i in range(self.roadmap_nodes):
            if i % 50 == 0:
                self._logger.info("Adding roadmap nodes: %d/%d", i, self.roadmap_nodes)
            self._add_state(self._parameters.random_state())

        self._roadmap.rebuild()

    def _add_state(self, state):
        cost = self._parameters.state_cost(state)

        if cost is None:
            return None

        node = _Node(state)

        forward_neighbors = []
        backward_neighbors = []

        for _, neighbor in itertools.islice(self._roadmap.nearest_neighbors((state.x, state.y)),
                                         self.neighbors_examined):
            neighbor_cost = self._parameters.state_cost(neighbor.state)

            path = local_planner.plan_path(state, neighbor.state)
            if path is not None:
                forward_neighbors.append((neighbor_cost * path.travel_time, neighbor))
                if path.travel_time < self.distance_epsilon:
                    return neighbor # Close enough node was already in the roadmap

            path = local_planner.plan_path(neighbor.state, state)
            if path is not None:
                backward_neighbors.append((neighbor_cost * path.travel_time, neighbor))
                if path.travel_time < self.distance_epsilon:
                    return neighbor # Close enough node was already in the roadmap

        forward_neighbors.sort()
        backward_neighbors.sort()

        for distance, neighbor in forward_neighbors[:self.max_neighbors]:
            self._maybe_connect(node, neighbor)

        for distance, neighbor in backward_neighbors[:self.max_neighbors]:
            self._maybe_connect(neighbor, node)

        self._roadmap.insert((state.x, state.y), node)
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

        node1.add_connection(node2, cost)

    def _path_cost(self, path_iterator, resolution = 0.1):
        """ Estimate integral of self._parameters.state_cost over the states on path_iterator. """

        # TODO: Maybe don't check points one by one, instead try midpoint, quarter points, ....
        # Halton sequence?

        cost = self._parameters.state_cost(path_iterator)
        if cost is None:
            return None

        while not path_iterator.finished():
            path_iterator.advance(resolution)

            state_cost = self._parameters.state_cost(path_iterator)
            if state_cost is None:
                return None
            else:
                cost += state_cost

        return cost

    def _get_connection_count(self):
        return sum(len(node[1].connections) for node in self._roadmap)

    def _path_smoothing(self, node_sequence):
        costs = []
        for i, (node1, node2) in enumerate(zip(node_sequence[:-1], node_sequence[1:])):
            for connection in node1.connections:
                if connection.node == node2:
                    costs.append(connection.cost)
                    break
            assert len(costs) == i + 1
        assert len(costs) == len(node_sequence) - 1

        for i in range(5 * len(node_sequence)):
            k = random.randrange(len(node_sequence))
            l = random.randrange(len(node_sequence))
            if k == l:
                continue

            k, l = min(k, l), max(k, l)

            if k + 1 == l:
                continue

            node1 = node_sequence[k]
            node2 = node_sequence[l]

            path = local_planner.plan_path(node1.state, node2.state)
            if path is None:
                continue
            cost = self._path_cost(path)
            if cost is None:
                continue

            previous_cost = sum(costs[k:l+1])
            if cost >= previous_cost:
                continue

            # Now we have a local path that is shorter than what the planner found
            # Replace it

            self._logger.info("Taking shortcut: skipping %i nodes, cost %d -> %d",
                              l - k - 1, previous_cost, cost)

            node_sequence = list(node_sequence[:k + 1] + node_sequence[l:])
            costs = list(costs[:k] + [cost] + costs[l:])
            assert len(costs) == len(node_sequence) - 1
        return node_sequence


class _PathIterator(path_iterator.PathIterator):
    def __init__(self, states):
        if len(states) < 2:
            raise ValueError("There must be at least two states.")
        self._states = states
        self.travel_time = sum(local_planner.plan_path(s1, s2).travel_time
                               for s1, s2
                               in zip(states[:-1], states[1:]))
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
                self._i = len(self._states) - 1
                self._time = self.travel_time
                self._sub.jump_to(self._sub.travel_time)
                return

            self._load_sub()

        assert(dt >= 0)
        assert(dt < self._sub.travel_time - self._sub.time)

        if dt == 0:
            return

        self._sub.advance(dt)

    def finished(self):
        return self._i == len(self._states) - 1 and self._sub.finished()

    def __getattr__(self, key):
        """ The rest of values gets taken from the sub iterator """
        return getattr(self._sub, key)
