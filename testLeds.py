import time
from neopixel import NeoPixel
from machine import Pin
numpix = 60
strip = NeoPixel(Pin(2, Pin.OUT), 10, 3, 1)

red = (255, 0, 0)
orange = (255, 165, 0)
yellow = (255, 150, 0)
green = (0, 255, 0)
blue = (0, 0, 255)
indigo = (75, 0, 130)
violet = (138, 43, 226)
colors_rgb = (red, orange, yellow, green, blue, indigo, violet)

# same colors as normaln rgb, just 0 added at the end
colors_rgbw = [color+tuple([0]) for color in colors_rgb]
colors_rgbw.append((0, 0, 0, 255))

# uncomment colors_rgb if you have RGB strip
# colors = colors_rgb
colors = colors_rgbw
strip.fill(red)