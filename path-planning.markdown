---
title: Path Planning Notes
layout: default
---

Here I'm putting stuff together for planning path of the robot locally (disregarding any
obstacles).
The goal is to have limited velocity, angular velocity, acceleration (magnitude of the
full 2D acceleration), angular acceleration, jerk (probably only second derivation of (scalar) speed?)
and angular jerk.

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
