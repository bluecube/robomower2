---
title: Path Planning
layout: default
---

The goal of the path planner is to be fast, and output paths with have limited
velocity, angular velocity, acceleration and jerk.
Additionally we also want to discourage paths that would use
[low wheel speed]({{ site.baseurl }}/motor-control.html#moral-of-the-story).

*In its present state this part doesn't work as great as I would like it to, and will probably be rewritten sooner or later.*

## State

Robot state is represented by its position, orientation, velocity, acceleration
and track curvature.

## Probabilistic Roadmap

As a path planner we use Probabilistic Roadmap.
This planner was selected, because it is capable of capturing all of the dynamics
requirements (at the cost of large number of large number of nodes in the roadmap.

This part is currently work in progress.

- We are using Halton sequences to generate the random waypoints.
- We limit the waypoints to have zero acceleration and curvature to reduce the dimensionality.

## Local Planner

Local planner's job is to find a reasonable connections between two pairs of states
without paying attention to map collisions or any of the dynamics limitations.

It works by first finding a path based only on the positions, orientations and curvatures
of the endpoint states.
This path is calculated as two degree 6 polynommials.

To simplify the conditions for these polynomials, we force the length of
derivations at the endpoints to a known value:

$$\sqrt{(\frac{\partial x}{\partial t}(0))^2 + (\frac{\partial y}{\partial t}(0))^2} = \frac{v(0) + \sqrt{(x(1) - x(0))^2 + (y(1) - y(0))^2}}{2}$$

The value was experimentlaly selected to be an arithmetic average of distance between the endpoints (in meters) and velocity
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

The local planner described in this section is implemented as a fairly general
[module]({{ site.repository_master }}/src_python/path_planning/local_planner.py) in the
repository, stateless and knowing nothing about the robot.

To be useable in the PRM planner, it needs collision checking added.
This functionality is implemented in a module called
[planning_parameters]({{ site.repository_master }}/src_python/path_planning/planning_parameters.py).
Planning parameters represent all of the path planner's knowledge about the robot and its
environment.
It provides a method to draw random samples on the map, and to calculate cost of being
in a state (which is infinite for colliding states).

As a final step, the notions of local path and state cost need to be combined to
determine whether a whole path is passable and what is its cost.
This is done in a method _path_cost
of the PRM module.

![Drunken pathfinder]({{ site.baseurl }}/img/2014-10/drunken-pathfinder.png)
