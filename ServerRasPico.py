from machine import Pin, Timer
import network
import time
import usocket as socket
import array
import rp2

SSID = 'MOVISTAR_F9CC'
SSID_KEY = 'v4vQiV5JKLQB5oVUd2rk'
LED_COL = 10
LED_AMP = 12


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


def initWifi() -> network.WLAN:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    return wlan


def wlanConnectCB(wlan, statusHandler):
    statusHandler.setStatus(StatusLed.NOT_CONNECTED)
    wlan.connect(SSID, SSID_KEY)


class LED_Strip:
    def __init__(self) -> None:
        self.strip = ws2812b(LED_COL * LED_AMP, 0, 6)
        self.colors = [128 for i in range(LED_AMP)]
        self.strip.fill(0, 0, 0)
        self.strip.show()

    def AmplitudesToLEDs(self, a: list) -> None:
        print(a)
        for j in range(LED_COL):
            amp = a[j]
            for led in range(LED_AMP):
                iRow = led if j % 2 == 1 else LED_AMP - led - 1
                if amp >= led:
                    self.strip.set_pixel(iRow + j * LED_AMP, 30, 0, 0)
                else:
                    self.strip.set_pixel(iRow + j * LED_AMP, 0, 0, 0)
        self.strip.show()


class StatusLed:
    NOT_CONNECTED = 0
    CONNECTING = 1
    CONNECTED = 2

    def __init__(self) -> None:
        self.pin = Pin('LED', Pin.OUT)
        self.status = StatusLed.NOT_CONNECTED
        Timer(period=500, mode=Timer.PERIODIC,
              callback=lambda t: self.__statusCB())

    def setStatus(self, status: int):
        self.status = status

    def __statusCB(self):
        if self.status == StatusLed.NOT_CONNECTED:
            self.pin.low()
        elif self.status == StatusLed.CONNECTING:
            self.pin.toggle()
        elif self.status == StatusLed.CONNECTED:
            self.pin.high()


class Server:
    def __init__(self) -> None:
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        # Bind the socket to the port
        server_address = ('192.168.1.40', 8002)
        print('starting up on {} port {}'.format(*server_address))
        self.sock.bind(server_address)
        self.sock.listen(1)

    def getLED_Amp(self, reciveCb):
        # Send data
        self.connection, client_address = self.sock.accept()
        while True:
            # Wait for a connection
            buffer = self.connection.recv(LED_COL)
            if len(buffer) == 0:
                continue
            b12 = buffer.decode()
            ledsAmp = [int(s, LED_AMP) for s in b12]
            reciveCb(ledsAmp)


def main():
    wlan = initWifi()
    wlan.connect(SSID, SSID_KEY)

    leds = LED_Strip()
    statusHandler = StatusLed()
    server = Server()

    while True:
        if not wlan.isconnected():
            if statusHandler.status == StatusLed.CONNECTING:
                continue
            statusHandler.setStatus(StatusLed.CONNECTING)
            Timer(period=5000, mode=Timer.ONE_SHOT,
                  callback=lambda t: wlanConnectCB(wlan, statusHandler))
            continue
        statusHandler.setStatus(StatusLed.CONNECTED)

        print(f'Server:{server.getLED_Amp(leds.AmplitudesToLEDs)}')


main()
