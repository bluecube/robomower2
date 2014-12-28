---
title: Path Following
layout: default
---

Once [path planner]({{ site.baseurl }}/path-planning.html) outputs a path, we need to
follow it.
The path itself provides velocity and curvature in every point, which are converted to
commands to the motor boards.

Because of path calculation inaccuracies (TODO: I would expect these to be really
small, why does it appear as a measurable effect?) and drive inaccuracies this commands
must be corected.

The correction works as follows:
We keep intended position as at given time as coordinates and heading.
Then we calculate forward, side and heading errors ($$e_F$$, $$e_S$$ and $$e_H$$
in the picture).

Forward velocity is modified by adding a multiple of $$e_F$$ and turn velocity is changed
by adding a multiple of $$e_S$$ and $$e_H$$.

The previous plan was to use PID controllers instead of only just the constants, but
this one works really well.

![Path following]({{ site.baseurl }}/img/2014-12/path-following.svg)

