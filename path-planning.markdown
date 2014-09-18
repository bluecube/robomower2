---
title: Path Planning Notes
layout: default
---

Here I'm putting stuff together for planning path of the robot locally (disregarding any
obstacles).
The goal is to have limited velocity, angular velocity, acceleration and jerk.

## Architecture

- Robot state $$(x, y, \phi, v, \omega, \ldots)$$
- Control limits (maximal speed, angular speed, acceleration, jerk,
  [minimal wheel speed]({{ site.baseurl }}/motor-control.html#moral-of-the-story)).
- [**Probablistic road map**](https://en.wikipedia.org/wiki/Probabilistic_roadmap).
- **Local planner** tries to connect two states in the path plan with some
  simple curve.
  Output of the local planner is checked if it doesn't exceed control limits,
  if it does, the path is not used.

## Local Planner Notes

[Currently]({{ site.repository_master }}/src_python/path_planning/local_planner.py)
the local planner calculates two polynomials of degree 3 for x and y coordinates.
The conditions are starting and ending position and derivation.

After that, the curve length is calculated by approximating it with polyline,
and driving time is calculated so that starting and ending velocities and accelerations
match the input states.

Then the limits are checked.
for velocity and angular acceleration the whole polynomial
has to be within limits (checked on the end points and in the roots of first derivation),
for angular velocity and acceleration, the limits are checked only in several regularly
points, reuglarly spaced through the travel time.

TODO: When selecting the X and Y polynomials, start and end curvature are not specified ->
it would be discontinuous when connecting the local paths.
I'll have to use degree 4 polynomials and put curvature into the robot state.
