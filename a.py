from machine import Pin, Timer
import network
import time
import usocket

SSID = 'MOVISTAR_F9CC'
SSID_KEY = 'v4vQiV5JKLQB5oVUd2rk'


def initWifi() -> network.WLAN:
    wlan = network.WLAN(network.STA_IF)
    wlan.active(True)
    return wlan


def wlanConnectCB(wlan, statusHandler):
    statusHandler.setStatus(StatusLed.NOT_CONNECTED)
    wlan.connect(SSID, SSID_KEY)


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


class Client:
    def __init__(self) -> None:
        self.sock = usocket.socket(usocket.AF_INET, usocket.SOCK_STREAM)

        # Connect the socket to the port where the server is listening
        server_address = ('192.168.1.35', 8001)
        self.sock.connect(server_address)

    def getLED_Amp(self):
        # Send data
        self.sock.sendall('LEDs')
        # Look for the response
        return int(self.sock.recv(16))


def main():
    wlan = initWifi()
    wlan.connect(SSID, SSID_KEY)

    statusHandler = StatusLed()
    client = Client()

    while True:
        if not wlan.isconnected():
            if statusHandler.status == StatusLed.CONNECTING:
                continue
            statusHandler.setStatus(StatusLed.CONNECTING)
            Timer(period=5000, mode=Timer.ONE_SHOT,
                  callback=lambda t: wlanConnectCB(wlan, statusHandler))
            continue
        statusHandler.setStatus(StatusLed.CONNECTED)
        print(f'Server:{client.getLED_Amp()}')
        time.sleep(1/30)


main()
