import math
import pygame.draw
from . import config

class MapWidget:
    def __init__(self, zoom):
        self._zoom = zoom
        self.samples = []
        self.offset = (0, 0)

    def draw(self, surface, x, y, w, h, mouse):
        scale = 1.1**self._zoom
        x_center = x + w // 2
        y_center = y + h // 2
        sample_radius = 10

        # Scale
        width_available = w / 5
        scale_value_step = 10 ** math.floor(math.log10(width_available / scale))
        scale_step = scale * scale_value_step
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

        # Samples
        for sample in self.samples:
            x = int((sample.x + self.offset[0]) * scale)
            y = -int((sample.y + self.offset[1]) * scale)

            if abs(x) > w/2 or abs(y) > h/2:
                continue

            x += x_center
            y += y_center

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
