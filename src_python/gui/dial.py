#!/usr/bin/python

from __future__ import division, print_function
from fltk import *
import math

class Dial(Fl_Widget):
    FONT_SIZE_RATIO = 0.035
    BAR_MARK_SIZE_RATIO = 0.03
    LINE_WIDTH_RATIO = 1 / 500

    def __init__(self, x, y, w, h, label=None):
        self.min_value = 0
        self.max_value = 100
        self.min_angle = 225
        self.max_angle = -45
        self.tick_step = 10
        self.tick_format = "%d"
        self.value_format = None

        Fl_Widget.__init__(self, x, y, w, h, label)

    def draw(self):
        size = min(self.w() - 3 * fl_height(), self.h() - fl_height())
        radius = int(0.4 * size)
        text_radius = 0.46 * size + 0.75 * fl_height()
        tick_radius = 0.43 * size + 2
        value_radius = int(0.2 * size)
        arrow_radius = 0.395 * size
        center_x = self.x() + self.w() // 2
        center_y = self.y() + self.h() // 2
        line_width = int(0.005 * size)

        fl_rectf(self.x(), self.y(), self.w(), self.h(), self.color())

        fl_color(self.labelcolor())
        fl_line_style(FL_SOLID, max(line_width, 2))

        fl_arc(center_x - radius, center_y - radius,
               2 * radius, 2 * radius,
               self.min_angle, self.max_angle)

        a = (self.max_angle - self.min_angle) * math.pi / (180 * self.max_value - self.min_value)
        b = self.min_angle * math.pi / 180 - self.min_value * a

        tick_count = (self.max_value - self.min_value) // self.tick_step
        tick_step_radians = self.tick_step * a
        min_angle_radians = self.min_angle * math.pi / 180
        for i in range(tick_count + 1):
            angle = i * tick_step_radians + min_angle_radians
            s = -math.sin(angle)
            c = math.cos(angle)

            fl_line(center_x + int(c * radius), center_y + int(s * radius),
                    center_x + int(c * tick_radius), center_y + int(s * tick_radius))

            text = self.tick_format % (self.min_value + i * self.tick_step)
            text_xoffset = int(fl_width(text)) // 2
            text_yoffset = int(fl_descent() - fl_height()) // 2
            fl_draw(text,
                    center_x + int(c * text_radius) - text_xoffset,
                    center_y + int(s * text_radius) - text_yoffset)

        text = (self.value_format or self.tick_format) % self.value
        fl_draw(text,
                center_x - int(fl_width(text)) // 2,
                center_y + value_radius)

        angle = a * self.value + b
        fl_line_style(FL_SOLID, max(2 * line_width, 3))
        fl_line(center_x, center_y,
                center_x + int(math.cos(angle) * arrow_radius),
                center_y - int(math.sin(angle) * arrow_radius))

    def resize(self, x, y, w, h):
        Fl_Widget.resize(self, x, y, w, h)


if __name__ == '__main__':
    window = Fl_Window(120, 120)
    dial = Dial(10, 10, 100, 100, "Dial")
    dial.value = 56
    dial.value_format = "%d %%"
    dial.tick_step = 50
    window.end()
    window.resizable(dial)
    window.show()
    Fl.run()
