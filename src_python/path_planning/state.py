import collections

State = collections.namedtuple('State', ['x', 'y', 'heading',
                                         'velocity', 'acceleration', 'curvature'])

def simple_state(x, y, heading):
    return State(x, y, heading, 0, 0, 0);
