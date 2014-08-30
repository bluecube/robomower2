---
title: Movement model & Calibration
layout: default
---

## Movement model

For localization, the robot will need (relatively) precise movement model.

The model we use is parametrized using five variables: $$(b, s_R, s_L, \sigma_R, \sigma_L)$$.
In this model the robot consists of two perfectly parallel wheels placed at
wheel base distance $$ b $$ from each other.
$$ s_R $$ and $$ s_L $$ are distance travelled per encoder tick for each wheel.
These values are not necessarily equal (because of manufacturing inaccuracies).
Distance measurement uncertainty is modelled using a Gaussian random variable for
each wheel.

Odometry values come every interval in the form of encoder ticks, counts
for left and right wheel are $$ n_R $$ and $$ n_L $$.
Distance travelled by a wheel is from a following distributions:
$$ d_{R, L} \sim n_{R, L}s_{R, L}N(0, \sigma_{R, L}) $$

During a single interval the robot is assumed to travel on a circular arc with length
$$ d = \frac{d_R + d_L}{2} $$ and angle $$ \alpha = \frac{d_R - d_L}{b} $$.

![Differential drive model]({{ site.baseurl }}/img/2014-08/diff-drive-model.svg)

Code that handles the calculations mentioned in this section is in the file
[differential_drive.py]({{ site.repository_master }}/src_python/differential_drive.py)

## Drive calibration

Because of manufacturing inaccuracies, I don't know the precise dimensions of the robot.
To do this, I wrote a tool that matches replays to known travelled pattern
([calibration.py]({{ site.repository_master }}/src_python/calibration.py)).

**WRITE THIS!**

![Calibration pattern]({{ site.baseurl }}/img/2014-08/calibration-pattern.svg)
