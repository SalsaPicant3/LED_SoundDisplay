import pyaudiowpatch as pyaudio
import time
import numpy as np
from threading import Thread
import socket
import queue

FORMAT = pyaudio.paInt16
x = 0
MAX_Amp = 2e5


def listToBaseTwelf(l: list):
    return ''.join([hex(min(round(i), 11)).replace('0x', '') for i in l])


def CalcFFT(data, sock, cubuDeErrors):
    try:
        npArrayData = np.frombuffer(data, dtype=np.int16)
        fftData = np.abs(np.fft.rfft(npArrayData))  # Max index es CHUNK
        fftData = fftData[:fftData.shape[0]//2+1]
        # Index de frequencies tretes de audio.py
        splitIndex = [0, 4, 7, 13, 26, 51, 101, 201, 401, 801]
        splitedFFT = np.split(fftData, splitIndex)
        avgFFT = np.array([np.max(i) for i in splitedFFT[1:]])/MAX_Amp
        sock.sendall(listToBaseTwelf(avgFFT).encode())
    except Exception as e:

        cubuDeErrors.put(e)


def getSpeakers(p) -> dict:
    try:
        # Get default WASAPI info
        wasapi_info = p.get_host_api_info_by_type(pyaudio.paWASAPI)
    except OSError:
        print(
            "Looks like WASAPI is not available on the system. Exiting...")
        exit()
    # Get default WASAPI speakers
    default_speakers = p.get_device_info_by_index(
        wasapi_info["defaultOutputDevice"])

    if not default_speakers["isLoopbackDevice"]:
        for loopback in p.get_loopback_device_info_generator():
            """
            Try to find loopback device with same name(and [Loopback suffix]).
            Unfortunately, this is the most adequate way at the moment.
            """
            if default_speakers["name"] in loopback["name"]:
                default_speakers = loopback
                break
        else:
            print(
                "Default loopback output device not found.\n\nRun `python -m pyaudiowpatch` to check available devices.\nExiting...\n")

            exit()
    return default_speakers


def setupClient() -> socket.socket:
    # Create a TCP/IP socket
    print('Creating new socket')
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)
    return sock

    # Connect the socket to the port where the server is listening


def connectSocket(sock):
    try:
        server_address = ('192.168.1.40', 8002)
        sock.connect(server_address)
        print('Conected to {} port {}'.format(*server_address))
        return True
    except Exception as e:
        print('Connection Fail', e)
        return False


if __name__ == "__main__":
    carretoDeErrors = queue.Queue()

    with pyaudio.PyAudio() as p:
        try:
            default_speakers = getSpeakers(p)
            print(
                f"Recording from: ({default_speakers['index']}){default_speakers['name']}")

            CHANNELS = default_speakers["maxInputChannels"]
            RATE = int(default_speakers["defaultSampleRate"])
            frames_per_buffer = pyaudio.get_sample_size(pyaudio.paInt16)
            READ_FREQUENCY = 15
            CHUNK = RATE // READ_FREQUENCY  # RATE / number of updates per second

            stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=RATE, input=True,
                            frames_per_buffer=CHUNK, input_device_index=default_speakers["index"])
            sock = setupClient()
            while True:
                if not connectSocket(sock):
                    time.sleep(2)
                    continue
                print('Socket connected')
                while True:
                    data = stream.read(CHUNK)
                    thCalcFFT = Thread(target=CalcFFT, args=(
                        data, sock, carretoDeErrors, ))
                    thCalcFFT.start()
                    if carretoDeErrors.empty():
                        continue
                    while not carretoDeErrors.empty():
                        carretoDeErrors.get()
                        print('Error amb socket creat')
                    sock.close()
                    sock = setupClient()
                    break
                time.sleep(2)

        except Exception as e:
            sock.close()
            stream.stop_stream()
            stream.close()
            p.terminate()
            print(e)
