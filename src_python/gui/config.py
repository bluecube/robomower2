from pygame.color import Color

try:
    import pygame.ftfont as _pygame_font
except ImportError:
    import pygame.font as _pygame_font

_pygame_font.init()

font = _pygame_font.SysFont('dejavusansmono', 12)
large_font = _pygame_font.SysFont('dejavusansmono', 24)

bgcolor = (0, 0, 0)
color1 = Color(0xcc, 0xcc, 0xcc)
color2 = Color(0xff, 0x00, 0x00)
