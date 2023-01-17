from machine import Pin, Timer
import network
import time
import usocket as socket

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
            buffer = self.connection.recv(16)
            if len(buffer) == 0:
                continue
            b12 = buffer.decode()
            ledsAmp = [int(s, 12) for s in b12]
            reciveCb(ledsAmp)


def main():
    wlan = initWifi()
    wlan.connect(SSID, SSID_KEY)

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
        print(f'Server:{server.getLED_Amp()}')


main()
