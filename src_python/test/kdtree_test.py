from nose.tools import *
from kdtree import *
import math
import random

def iterator_test():
    """ Test that the tree is not losing any values when splitting leaves
    and rebuilding; check that nearest_neighbors eventualy return everything"""
    random.seed(0)
    count = 500

    tree = KdTree()
    for i in range(count):
        x = random.uniform(0, 100)
        y = random.uniform(0, 100)
        tree.insert((x, y), i)

    assert_equal(sorted(value for coord, value in tree), list(range(count)))

    tree.rebuild()

    assert_equal(sorted(value for coord, value in tree), list(range(count)))

def check_sequence_increasing(seq):
    seq = list(seq)
    for prev, current in zip(seq[:-1], seq[1:]):
        assert prev < current

def nearest_neighbor_test():
    random.seed(0)
    count = 4

    tree = KdTree()
    for i in range(count):
        x = random.uniform(0, 100)
        y = random.uniform(0, 100)
        tree.insert((x, y), i)

    #print()
    #tree.pprint()
    neighbors = list(tree.nearest_neighbors((30, 30)))

    assert_equal(sorted(value for coord, value in neighbors), list(range(count)))
    check_sequence_increasing(math.hypot(coord[0] - 30, coord[1] - 30)
                              for coord, value
                              in neighbors)

    tree.rebuild()

    neighbors = list(tree.nearest_neighbors((30, 30)))
    assert_equal(sorted(value for coord, value in neighbors), list(range(count)))
    check_sequence_increasing(math.hypot(coord[0] - 30, coord[1] - 30)
                              for coord, value
                              in neighbors)
