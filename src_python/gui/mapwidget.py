import math
import pygame.draw
from . import config

class MapWidget:
    def __init__(self, zoom):
        self._zoom = zoom
        self.zoom(0)
        self.samples = []
        self.offset = (0, 0)

        self.lines = None
        self.polygons = None

    def draw(self, surface, x, y, w, h, mouse):
        x_center = x + w // 2
        y_center = y + h // 2

        def projection(xx, yy):
            xx = x_center + int((xx + self.offset[0]) * self._scale)
            yy = y_center - int((yy + self.offset[1]) * self._scale)

            return xx, yy

        # Scale
        width_available = w / 5
        scale_value_step = 10 ** math.floor(math.log10(width_available / self._scale))
        scale_step = self._scale * scale_value_step
        scale_ticks = int(math.floor(width_available / scale_step))
        if scale_ticks == 1:
            scale_value_step /= 10
            scale_step /= 10
            scale_ticks *= 10

        size = scale_ticks * scale_value_step
        if size >= 1:
            size = "{:d} m".format(int(size))
        else:
            size = "{:.0e} m".format(size)
        text = config.font.render(size,
                                  antialias=True,
                                  color=config.color1,
                                  background=config.bgcolor)
        surface.blit(text, (x + w - text.get_width(), y + h - text.get_height()))
        x_offset = x + w - text.get_width() - config.font.get_height() // 2 - scale_ticks * scale_step
        y_offset = y + h - 3 * text.get_height() // 4

        for i in range(scale_ticks):
            pygame.draw.rect(surface, config.color1, pygame.Rect(x_offset + i * scale_step,
                                                                 y_offset,
                                                                 scale_step + 1, text.get_height() // 2),
                             i % 2)

        # extra polygons
        if self.polygons is not None:
            for polygon in self.polygons:
                projected = [projection(x, y) for x, y in polygon]
                pygame.draw.polygon(surface, config.color1_50, projected)
                pygame.draw.lines(surface, config.color1, True, projected)

        # extra lines
        if self.lines is not None:
            for i, line in enumerate(reversed(self.lines)):
                if len(line) == 0:
                    continue
                projected = [projection(x, y) for x, y in line]
                if i == len(self.lines) - 1:
                    color = config.color2
                else:
                    color = config.color1_50
                pygame.draw.lines(surface, color, False, projected)
                for pos in projected:
                    pygame.draw.circle(surface, color, pos, 2, 1)

        # Samples
        if len(self.samples) > 0:
            sample_radius = max(5, min(10, math.sqrt(10**2 / len(self.samples) / 10)))

        for sample in self.samples:
            x, y = projection(sample.x, sample.y)

            c = int(math.cos(sample.heading) * sample_radius)
            s = int(math.sin(sample.heading) * sample_radius)
            pygame.draw.polygon(surface, config.color1,
                                [(x + c, y - s),
                                 (x + (s - c) // 2, y - (- c - s) // 2),
                                 (x + (- s - c) // 2, y - (c - s) // 2)])

        # Cross
        cross = min(w, h) / 30
        pygame.draw.line(surface, config.color2,
                         (x_center - cross, y_center), (x_center + cross, y_center))
        pygame.draw.line(surface, config.color2,
                         (x_center, y_center - cross), (x_center, y_center + cross))

    def zoom(self, step):
        self._zoom += step
        self._scale = 1.1**self._zoom
