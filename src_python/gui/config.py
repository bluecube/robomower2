from pygame.color import Color as _Color
try:
    import pygame.ftfont as _pygame_font
except ImportError:
    import pygame.font as _pygame_font

_pygame_font.init()

font = _pygame_font.SysFont('dejavusansmono', 12)
large_font = _pygame_font.SysFont('dejavusansmono', 24)

bgcolor = _Color(0, 0, 0)
color1 = _Color(0xcc, 0xcc, 0xcc)
color1_50 = _Color(0x66, 0x66, 0x66)
color2 = _Color(0xff, 0x00, 0x00)
