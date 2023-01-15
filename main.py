import network
from time import sleep
import urequests as requests
import array
import time
from machine import Pin
import rp2


@rp2.asm_pio(sideset_init=rp2.PIO.OUT_LOW, out_shiftdir=rp2.PIO.SHIFT_LEFT, autopull=True, pull_thresh=24)
def ws2812():
    T1 = 2
    T2 = 5
    T3 = 3
    wrap_target()
    label("bitloop")
    out(x, 1)               .side(0)[T3 - 1]
    jmp(not_x, "do_zero")   .side(1)[T1 - 1]
    jmp("bitloop")          .side(1)[T2 - 1]
    label("do_zero")
    nop()                   .side(0)[T2 - 1]
    wrap()

# delay here is the reset time. You need a pause to reset the LED strip back to the initial LED
# however, if you have quite a bit of processing to do before the next time you update the strip
# you could put in delay=0 (or a lower delay)


class ws2812b:
    def __init__(self, num_leds, state_machine, pin, delay=0.001):
        self.pixels = array.array("I", [0 for _ in range(num_leds)])
        self.sm = rp2.StateMachine(
            state_machine, ws2812, freq=8000000, sideset_base=Pin(pin))
        self.sm.active(1)
        self.num_leds = num_leds
        self.delay = delay
        self.brightnessvalue = 255

    # Set the overal value to adjust brightness when updating leds
    def brightness(self, brightness=None):
        if brightness == None:
            return self.brightnessvalue
        else:
            if (brightness < 1):
                brightness = 1
        if (brightness > 255):
            brightness = 255
        self.brightnessvalue = brightness

      # Create a gradient with two RGB colors between "pixel1" and "pixel2" (inclusive)
    def set_pixel_line_gradient(self, pixel1, pixel2, left_red, left_green, left_blue, right_red, right_green, right_blue):
        if pixel2 - pixel1 == 0:
            return

        right_pixel = max(pixel1, pixel2)
        left_pixel = min(pixel1, pixel2)

        for i in range(right_pixel - left_pixel + 1):
            fraction = i / (right_pixel - left_pixel)
            red = round((right_red - left_red) * fraction + left_red)
            green = round((right_green - left_green) * fraction + left_green)
            blue = round((right_blue - left_blue) * fraction + left_blue)

            self.set_pixel(left_pixel + i, red, green, blue)

      # Set an array of pixels starting from "pixel1" to "pixel2" to the desired color.
    def set_pixel_line(self, pixel1, pixel2, red, green, blue):
        for i in range(pixel1, pixel2+1):
            self.set_pixel(i, red, green, blue)

    def set_pixel(self, pixel_num, red, green, blue):
        # Adjust color values with brightnesslevel
        blue = round(blue * (self.brightness() / 255))
        red = round(red * (self.brightness() / 255))
        green = round(green * (self.brightness() / 255))

        self.pixels[pixel_num] = blue | red << 8 | green << 16

    # rotate x pixels to the left
    def rotate_left(self, num_of_pixels):
        if num_of_pixels == None:
            num_of_pixels = 1
        self.pixels = self.pixels[num_of_pixels:] + self.pixels[:num_of_pixels]

    # rotate x pixels to the right
    def rotate_right(self, num_of_pixels):
        if num_of_pixels == None:
            num_of_pixels = 1
        num_of_pixels = -1 * num_of_pixels
        self.pixels = self.pixels[num_of_pixels:] + self.pixels[:num_of_pixels]

    def show(self):
        for i in range(self.num_leds):
            self.sm.put(self.pixels[i], 8)
        time.sleep(self.delay)

    def fill(self, red, green, blue):
        for i in range(self.num_leds):
            self.set_pixel(i, red, green, blue)
        time.sleep(self.delay)


apiID = '192.168.1.35'
nCols = 5
nRows = 12
nLED = nRows * nCols

RED = (255, 0, 0)
ORANGE = (255, 165, 0)
YELLOW = (255, 150, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
INDIGO = (75, 0, 130)
VIOLET = (138, 43, 226)


def connect(wlan: network.WLAN):


def getAPI() -> None | str:
    try:
        res = requests.get(url=f"http://192.168.1.35:8000/LED_AMP")
        return res.text
    except OSError:
        return None


def thWifi():
    strip = ws2812b(nLED, 0, 2)
    strip.fill(0, 150, 0)
    strip.show()
    LED_Gradiant = array.array("I", [0 for _ in range(nRows)])
    initLED_Gradiant(strip, LED_Gradiant)
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    connect(wlan)
    while True:
        conected = wlan.isconnected()
        if not conected:
            sleep(10)
            connect(wlan)
            continue
        # Wi-fi connected
        response = getAPI()
        if response is None:
            sleep(5)
            continue
        API_msg_To_LED_array(response, strip, LED_Gradiant)
        sleep(1/30)


def API_msg_To_LED_array(msg: str, strip: ws2812b, LED_Gradiant: array.array):
    splitedMsg = [int(i) for i in msg.replace('"', '').split('.')]
    for j in range(0, min(nCols, len(splitedMsg))):
        for i in range(0, nRows):
            rowIndex = i if j % 2 == 0 else nRows - i - 1  # Reversed if odd
            color = LED_Gradiant[rowIndex]

            strip.pixels[i + j *
                         nCols] = color if splitedMsg[j] >= rowIndex else 0

    strip.show()


def initLED_Gradiant(strip: ws2812b, arraypr: array.array):
    firstColor = RED
    secondColor = YELLOW
    thirdColor = GREEN
    strip.set_pixel_line_gradient(
        0, nRows//2-1, firstColor[0], firstColor[1], firstColor[2], secondColor[0], secondColor[1], secondColor[2])
    strip.set_pixel_line_gradient(
        nRows//2, nRows-1, secondColor[0], secondColor[1], secondColor[2], thirdColor[0], thirdColor[1], thirdColor[2])
    for i in range(nRows):
        arraypr[i] = strip.pixels[i]


if __name__ == '__main__':
    print('Stating')
    thWifi()
    print('Ending?')
