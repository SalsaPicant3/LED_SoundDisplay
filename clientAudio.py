import pyaudiowpatch as pyaudio
import time
import numpy as np
import matplotlib.pyplot as plt
from threading import Thread
import socket

FORMAT = pyaudio.paInt16
x = 0
MAX_Amp = 6e4


def listToBaseTwelf(l: list):
    return ''.join([hex(min(round(i), 11)).replace('0x', '') for i in l])


def CalcFFT(data, nBars, maxIndex, sock):
    t1 = time.time()
    # type: ignore
    npArrayData = np.fromstring(data, dtype=np.int16)
    fftData = np.abs(np.fft.rfft(npArrayData))  # Max index es CHUNK
    fftData = fftData[:fftData.shape[0]//2+1]
    splitIndex = np.geomspace(1, maxIndex, nBars, dtype=np.int16)
    splitedFFT = np.split(fftData, splitIndex)
    avgFFT = np.array([np.max(i) for i in splitedFFT[1:]])/MAX_Amp
    sock.sendall(listToBaseTwelf(avgFFT).encode())
    print("took %.02f ms" % ((time.time()-t1)*1000))


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
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    # Connect the socket to the port where the server is listening
    server_address = ('192.168.1.40', 8002)
    print('connecting to {} port {}'.format(*server_address))
    sock.connect(server_address)
    return sock


if __name__ == "__main__":

    sock = setupClient()

    with pyaudio.PyAudio() as p:
        default_speakers = getSpeakers(p)
        print(
            f"Recording from: ({default_speakers['index']}){default_speakers['name']}")

        CHANNELS = default_speakers["maxInputChannels"]
        RATE = int(default_speakers["defaultSampleRate"])
        frames_per_buffer = pyaudio.get_sample_size(pyaudio.paInt16)
        READ_FREQUENCY = 10
        CHUNK = RATE // READ_FREQUENCY  # RATE / number of updates per second
        RECORD_SECONDS = 200
        nBars = 10
        fMax = 6e3
        maxIndex = (CHUNK * fMax) // RATE

        stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=RATE, input=True,
                        frames_per_buffer=CHUNK, input_device_index=default_speakers["index"])

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            thCalcFFT = Thread(target=CalcFFT, args=(
                data, nBars, maxIndex, sock,))
            thCalcFFT.start()

        stream.stop_stream()
        stream.close()
        p.terminate()
