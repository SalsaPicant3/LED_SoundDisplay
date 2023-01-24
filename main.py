from machine import Pin, Timer
import network
import time
import usocket as socket
import array
import rp2
from math import floor

LED_COL = 10
LED_AMP = 12
LED_REFRESH_FREQ = 20


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


class Wifi:
    def __init__(self) -> None:
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)

    def connect(self):
        SSID = 'MOVISTAR_F9CC'
        SSID_KEY = 'v4vQiV5JKLQB5oVUd2rk'
        self.wlan.connect(SSID, SSID_KEY)
        return self.isconnected()

    def isconnected(self):
        return self.wlan.isconnected()


class LED_Strip:
    OFF = 0
    MID = 1
    ON = 2

    def __init__(self) -> None:
        self.strip = ws2812b(LED_COL * LED_AMP, 0, 6)
        self.colors = [0x000080, 0x000b75, 0x00156b, 0x002060, 0x002b55,
                       0x00354b, 0x004040, 0x004033, 0x004026, 0x00401a, 0x00400d, 0x004000]
        self.strip.fill(0, 0, 0)
        self.strip.show()
        self.enableShow = False

    def AmplitudesToLEDs(self, a: list) -> None:
        def genRowIndex(colIndex, amp) -> list:
            b = list()
            for led in range(LED_AMP):
                iRow = led if colIndex % 2 == 1 else LED_AMP - led - 1
                index = iRow + colIndex * LED_AMP
                b.append((index, amp >= led, self.strip.pixels[index] != 0))
            return b
        for col in range(LED_COL):
            amp = a[col]
            data = genRowIndex(col, amp)
            for i in range(LED_AMP):
                iPixel, LED_ON, currentLED_ON = data[i]
                if i == LED_AMP - 1:  # Last led is different
                    nextLED_ON = False
                else:
                    nextLED_ON = data[i+1][2]

                if LED_ON:
                    self.strip.pixels[iPixel] = self.colors[i]
                else:
                    if currentLED_ON and not nextLED_ON:
                        self.strip.pixels[iPixel] = 0

        if self.enableShow:
            self.enableShow = False
            self.strip.show()

    def statusCONNECTED_CB(self):
        self.enableShow = True

    def statusNO_CON_CB(self):
        self.strip.fill(0, 0, 0)
        self.strip.show()


class StatusLed:
    NO_WIFI = 0
    NO_SOCKET = 1
    CONNECTED = 2

    def __init__(self) -> None:
        self.pin = Pin('LED', Pin.OUT)
        self.status = StatusLed.NO_WIFI
        Timer(period=500, mode=Timer.PERIODIC,
              callback=lambda t: self.__statusCB())
        self.cbFunc = list()
        Timer(period=1000//LED_REFRESH_FREQ, mode=Timer.PERIODIC,
              callback=lambda t: self.__functionCB())

    def setStatus(self, status: int):
        self.status = status

    def setCBfunc(self, state, func):
        self.cbFunc.append((state, func))

    def __functionCB(self):
        for state, funct in self.cbFunc:
            if state == self.status:
                funct()

    def __statusCB(self):
        if self.status == StatusLed.NO_WIFI:
            self.pin.low()
        elif self.status == StatusLed.NO_SOCKET:
            self.pin.toggle()
        elif self.status == StatusLed.CONNECTED:
            self.pin.high()


class Server:
    WAITING_CONNECTION_TIMEOUT = 1  # Seconds
    CLIENT_DATA_TIMEOUT = 2000  # ms
    ADDRESS = ('192.168.1.40', 8002)

    def __init__(self) -> None:
        self.sock = None
        self.clientTimer = None

    def createSocket(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.settimeout(Server.WAITING_CONNECTION_TIMEOUT)
        self.sock.bind(Server.ADDRESS)
        self.sock.listen(1)
        self.oldTime = time.ticks_ms()

    def closeSocket(self):
        if self.sock is not None:
            self.sock.close()
            self.sock = None

    def createConnection(self) -> bool:
        """
        BLOCKING FUNCTION
        """
        try:
            self.connection, client_address = self.sock.accept()
            self.oldTime = time.ticks_ms()
        except OSError:
            return False
        return True

    def closeConnection(self):
        self.connection.close()

    def getClientData(self, reciveCb):
        try:
            buffer = self.connection.recv(LED_COL)
        except OSError as e:
            if e.errno == 110:
                return time.ticks_ms() - self.oldTime >= Server.CLIENT_DATA_TIMEOUT
            raise
        if len(buffer) == 0:
            return time.ticks_ms() - self.oldTime >= Server.CLIENT_DATA_TIMEOUT
        b12 = buffer.decode()
        ledsAmp = [int(s, LED_AMP) for s in b12]
        reciveCb(ledsAmp)
        self.oldTime = time.ticks_ms()
        return True


def main():
    wifi = Wifi()
    leds = LED_Strip()
    status = StatusLed()
    server = Server()
    status.setCBfunc(StatusLed.CONNECTED, leds.statusCONNECTED_CB)
    status.setCBfunc(StatusLed.NO_SOCKET, leds.statusNO_CON_CB)
    status.setCBfunc(StatusLed.NO_WIFI,   leds.statusNO_CON_CB)

    while True:
        if status.status == StatusLed.NO_WIFI:
            wifiConnected = wifi.connect()
            if wifiConnected:
                server.createSocket()
                status.setStatus(StatusLed.NO_SOCKET)
                continue
            time.sleep(5)

        elif status.status == StatusLed.NO_SOCKET:
            socketConnected = server.createConnection()
            if socketConnected:
                status.setStatus(StatusLed.CONNECTED)
            if not wifi.isconnected():
                server.closeSocket()
                status.setStatus(StatusLed.NO_WIFI)

        elif status.status == StatusLed.CONNECTED:
            clientAlive = server.getClientData(leds.AmplitudesToLEDs)
            if not clientAlive:
                server.closeConnection()
                status.setStatus(StatusLed.NO_SOCKET)


main()
