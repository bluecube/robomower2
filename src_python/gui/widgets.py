import math
import logging
import collections
import pygame.draw
from . import config

class Dial:
    MIN_ANGLE = (5 / 4) * math.pi
    MAX_ANGLE = - math.pi / 4

    def __init__(self, label, min_value=0, max_value=100, tick_format="%d", value_format=None, unit=None):
        self.label = label
        self.value = 0;
        self.min_value = min_value
        self.max_value = max_value
        self.tick_format = tick_format
        self.value_format = value_format
        self.unit = unit

    def draw(self, surface, x, y, w, h, mouse):
        font_height = config.font.get_height()
        size = min(w - font_height, h)
        radius = int(0.5 * size)
        text_radius = 0.57 * size + 0.75 * font_height
        tick_radius = 0.55 * size + 0.2 * font_height
        label_radius = int(0.1 * size)
        arrow_radius = 0.45 * size
        center_radius = 0.04 * size
        center_x = x + w // 2
        center_y = y + h // 2

        # Value large number
        text = config.large_font.render((self.value_format or self.tick_format) % self.value,
                                          antialias=True,
                                          color=config.color1,
                                          background=config.bgcolor)
        surface.blit(text,
                     (center_x + - text.get_width() // 2, center_y + label_radius))

        # unit
        if self.unit:
            text = config.font.render(self.unit,
                                        antialias=True,
                                        color=config.color1,
                                        background=config.bgcolor)
            surface.blit(text,
                         (center_x + - text.get_width() // 2,
                          center_y + label_radius + config.large_font.get_linesize()))

        # Label
        if self.label:
            text = config.font.render(self.label,
                                        antialias=True,
                                        color=config.color1,
                                        background=config.bgcolor)
            surface.blit(text,
                         (center_x + - text.get_width() // 2, center_y - label_radius - text.get_height()))

        # minimum tick
        s = -math.sin(self.MIN_ANGLE)
        c = math.cos(self.MIN_ANGLE)
        text = config.font.render(self.tick_format % self.min_value,
                                    antialias=True,
                                    color=config.color1,
                                    background=config.bgcolor)
        surface.blit(text,
                     (center_x + int(c * text_radius) - text.get_width() // 2,
                      center_y + int(s * text_radius) - text.get_height() // 2))
        pygame.draw.aaline(surface,
                           config.color1,
                           (center_x + int(c * radius), center_y + int(s * radius)),
                           (center_x + int(c * tick_radius), center_y + int(s * tick_radius)))

        # maximum tick
        s = -math.sin(self.MAX_ANGLE)
        c = math.cos(self.MAX_ANGLE)
        text = config.font.render(self.tick_format % self.max_value,
                                    antialias=True,
                                    color=config.color1,
                                    background=config.bgcolor)
        surface.blit(text,
                     (center_x + int(c * text_radius) - text.get_width() // 2,
                      center_y + int(s * text_radius) - text.get_height() // 2))
        pygame.draw.aaline(surface,
                           config.color1,
                           (center_x + int(c * radius), center_y + int(s * radius)),
                           (center_x + int(c * tick_radius), center_y + int(s * tick_radius)))

        # center circle
        pygame.draw.circle(surface,
                           config.color1,
                           (center_x, center_y),
                           int(center_radius),
                           1)

        a = (self.MAX_ANGLE - self.MIN_ANGLE) / (self.max_value - self.min_value)
        b = self.MIN_ANGLE - self.min_value * a

        # arc
        pygame.draw.arc(surface,
                        config.color1,
                        pygame.Rect(center_x - radius, center_y - radius,
                                    2 * radius, 2 * radius),
                        min(self.MIN_ANGLE, self.MAX_ANGLE),
                        max(self.MIN_ANGLE, self.MAX_ANGLE),
                        1)

        # arrow
        angle = a * self.value + b
        pygame.draw.line(surface,
                         config.color2,
                         (center_x, center_y),
                         (center_x + int(math.cos(angle) * arrow_radius), center_y - int(math.sin(angle) * arrow_radius)),
                         3)


class Xy:
    def __init__(self, label, range_x = 1, range_y = 1, fmt_x = "%.2f", fmt_y = "%.2f"):
        self.label = label
        self.x = 0
        self.y = 0
        self.range_x = range_x
        self.range_y = range_y
        self.fmt_x = fmt_x
        self.fmt_y = fmt_y

    @property
    def label(self):
        if len(self._label) == 1:
            return self._label[0]
        else:
            return self._label

    @label.setter
    def label(self, value):
        if not value:
            self._label = []
        elif isinstance(value, str):
            self._label = [value]
        else:
            self._label = value

    def draw(self, surface, x, y, w, h, mouse):
        spacing = int(config.font.get_height() * 0.3)

        for i, row in enumerate(self._label):
            text = config.font.render(row,
                                      antialias=True,
                                      color=config.color1,
                                      background=config.bgcolor)
            surface.blit(text, (x + spacing, y + spacing + i * config.font.get_linesize()))

        text = config.font.render((self.fmt_x or "") % (self.x + 0),
                                  antialias=True,
                                  color=config.color1,
                                  background=config.bgcolor)
        surface.blit(text, (x + spacing,
                            y + h - spacing - text.get_height() - config.font.get_linesize()))

        text = config.font.render((self.fmt_y or "") % (self.y + 0),
                                  antialias=True,
                                  color=config.color1,
                                  background=config.bgcolor)
        surface.blit(text, (x + spacing,
                            y + h - spacing - text.get_height()))

        x_pos = int(x + (w - 1) * (1 + self.x / self.range_x) / 2)
        y_pos = int(y + (h - 1) * (1 - self.y / self.range_y) / 2)
        pygame.draw.line(surface, config.color2,
                         (x_pos, y), (x_pos, y + h))
        pygame.draw.line(surface, config.color2,
                         (x, y_pos), (x + w, y_pos))


class Grid:
    def __init__(self, columns, items, padding):
        self.columns = columns
        self.rows = (len(items) + columns - 1) // columns
        self.items = items
        self.padding = padding

    def draw(self, surface, x, y, w, h, mouse):
        item_width = int((w - (self.columns - 1) * self.padding) / self.columns)
        item_height = int((h - (self.rows - 1) * self.padding) / self.rows)

        iterator = iter(self.items)
        try:
            for i in range(self.columns):
                xx = x + item_width * i + self.padding * i
                for j in range(self.rows):
                    yy = y + item_height * j + self.padding * j
                    #pygame.draw.rect(surface, config.color1_50, pygame.Rect(xx, yy, item_width, item_height), 1)
                    next(iterator).draw(surface, xx, yy, item_width, item_height, mouse)
        except StopIteration:
            pass

class Slider:
    power = 4

    def __init__(self, label, min, max, fmt = "%.2f", power = 2):
        self.label = label
        self.value = min
        self._min = min
        self._max = max
        self.fmt = fmt
        self.callback = None
        self._power = power

    def _pseudolog(self, val):
        return val ** (1/self._power)

    def _pseudolog_inv(self, val):
        return val ** self._power

    def draw(self, surface, x, y, w, h, mouse):
        text = config.font.render(self.label,
                                  antialias=True,
                                  color=config.color1,
                                  background=config.bgcolor)
        surface.blit(text, (x + (w - text.get_width()) / 2,
                            y + h - text.get_height()))

        text = config.font.render(self.fmt % (self.value + 0),
                                  antialias=True,
                                  color=config.color1,
                                  background=config.bgcolor)
        bottom = y + h - text.get_height() - config.font.get_linesize()
        surface.blit(text, (x + (w - text.get_width()) / 2, bottom))

        rect_height = bottom - y;

        if mouse is not None and mouse[0] >= x and mouse[0] < x + w and \
           mouse[1] >= y and mouse[1] < bottom:
            self.value = self._min + (self._max - self._min) * self._pseudolog_inv((bottom - mouse[1]) / rect_height)
            if self.callback is not None:
                self.callback()

        value_height = int(rect_height * self._pseudolog((self.value - self._min) / (self._max - self._min)))

        pygame.draw.rect(surface, config.color1_50, pygame.Rect(x, bottom - value_height, w, value_height), 0)
        pygame.draw.rect(surface, config.color1, pygame.Rect(x, y, w, rect_height), 1)

class LogWidget(logging.Handler):
    def __init__(self, bottom_to_top):
        super().__init__()
        self._lines = collections.deque()
        self._bottom_to_top = bottom_to_top

    def emit(self, record):
        self.add_line(self.format(record), record.levelno >= logging.WARNING)

    def add_line(self, string, red):
        self._lines.append((string, red))

    def draw(self, surface, x, y, w, h, mouse):
        lines = int(h / config.font.get_linesize())
        for i in range(len(self._lines) - lines):
            self._lines.popleft()

        if self._bottom_to_top:
            y += h - len(self._lines) * config.font.get_linesize()

        for string, red in self._lines:
            color = config.color2 if red else config.color1

            text = config.font.render(string,
                                      antialias=True,
                                      color=color,
                                      background=config.bgcolor)
            surface.blit(text, (x, y))
            y += config.font.get_linesize()
