import collections

State = collections.namedtuple('State', ['x', 'y', 'heading',
                                         'velocity', 'acceleration', 'curvature'])
