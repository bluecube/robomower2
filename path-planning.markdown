---
title: Path Planning Notes
layout: default
---

Here I'm putting stuff together for planning path of the robot locally (disregarding any
obstacles).
The goal is to have limited velocity, angular velocity, acceleration (magnitude of the
full 2D acceleration), angular acceleration, jerk (probably only second derivation of (scalar) speed?)
and angular jerk.

## Architecture

- Robot state $$(x, y, \phi, v, \omega, \ldots)$$
- Control limits (maximal speed, angular speed, acceleration, angular acceleration,
  jerk, angular jerk,
  [minimal wheel speed]({{ site.baseurl }}/motor-control.html#moral-of-the-story)).
- Working area is split into convex blocks.
- **High level planner** has only a graph of these blocks with edges weighted by
  distance + extra cost.
- **Local planner** tries to connect two states in the path plan with some
  simple curve (interval of max negative jerk, interval of max positive jerk for
  both angular and linear speeds??).
  Output of the local planner is checked if it doesn't exceed control limits,
  if it does, the path is not used.
- **Detailed planner**; probably some variation of RRT. Uses local planner inside.
- Algorithm:
    - Find path through the convex blocks using the high level planner
    - Use the local planner to find control inputs to go through the rough path
      from the previous step at some constant cruise speed.
    - If local planner fails, use the detailed planner for this block only
      (or several surrounding blocks, this needs some more thinking).

## Notes

These are just some notes.
I need to read a lot more stuff before implementing any of this.

| | Notes
| ---
| $$ \vec{x} = (x, y) $$ | position
| $$ \phi $$ | orientation
| ---
| $$ v $$ | speed |
| $$ \vec{x}' = v \cdot (cos \phi, sin \phi) $$ | velocity
| $$ \phi' $$ | angular velocity
| ---
| $$ \vec{x}'' = v' \phi'  \cdot (- sin \phi, cos \phi) $$ | acceleration
| $$ \vert \vec{x}'' \vert = v' \phi' $$
| $$ \phi'' $$ | angular acceleration
| ---
| $$ \vert \vec{x}' \vert'' = v'' $$ | jerk (a) |
| $$ \vert \vec{x}'' \vert' = v'' \phi' + v' \phi'' $$ | jerk (b) |
| $$ \vert \vec{x}''' \vert = \text{something complicated} $$ | jerk (c) |
| $$ \phi''' $$ | angular jerk
