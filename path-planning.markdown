---
title: Path Planning
layout: default
---

The goal of the path planner is to be fast, and output paths with have limited
velocity, angular velocity, acceleration and jerk.
Additionally we also want to discourage paths that would use
[low wheel speed]({{ site.baseurl }}/motor-control.html#moral-of-the-story).

## State

Robot state is represented by its position, orientation, velocity, acceleration
and track curvature.

## Local Planner

Local planner's job is to find a reasonable connections between two pairs of states
without paying attention to map collisions or any of the dynamics limitations.

It works by first finding a path based only on the positions, orientations and curvatures
of the endpoint states.
This path is calculated as two degree 6 polynommials.

To simplify the conditions for these polynomials, we calculate the length of
second derivations $$\sqrt{(\frac{\partial x}{\partial t})^2, (\frac{\partial x}{\partial t})^2}$$
to a known value.

The method to find this value was experimentlaly selected to be
an arithmetic average of distance between the endpoints (in meters) and velocity
in endpoints (in meters / second).

Once the paht is known, we calculate its length, travel time (based on endpoint velocities
and accelerations) and a polynomial that controls the velocity.

The Path iterator structure that is used to represent the resulting path is indexed in seconds,
which means that we have to convert between the time and curve parameter for the path
polynomials.
This is done in two steps.
First we use the integral of velocity polynomial to obtain distance at given time.
For the second step we store distances at regular intervals of curve parameter and
interpolate.

## Probabilistic Roadmap

![Drunken pathfinder]({{ site.baseurl }}/img/2014-10/drunken-pathfinder.png)
