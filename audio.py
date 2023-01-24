"""A simple example of recording from speakers ('What you hear') using the WASAPI loopback device"""

# Spinner is a helper class that is in the same examples folder.
# It is optional, you can safely delete the code associated with it.

import pyaudiowpatch as pyaudio
import time
import wave
import time
import numpy as np
import time
import wave
import matplotlib.pyplot as plt
from threading import Thread

# open stream
FORMAT = pyaudio.paInt16
#CHANNELS = 1
#RATE = 44100
#
# CHUNK = 2048 # RATE / number of updates per second
#
#RECORD_SECONDS = 20

x = 0
# use a Blackman window


def wantedF2Index(fftTime):
    a = []
    wantedF = [0, 32, 64, 125, 250, 500, 1000, 2000, 4000, 8000]
    for i, f in enumerate(fftTime):
        if f > wantedF[len(a)]:
            a.append(i)
            if len(a) == len(wantedF):
                return a


def ampTuned(x): return min(12, 12*x/(20000 + x))


def soundPlot(data, ax1, ax2, ax3, ax4, CHUNK, RATE):
    t1 = time.time()
    npArrayData = np.fromstring(data, dtype=np.int16)
    indata = npArrayData
    # Plot time domain
    ax1.cla()
    ax1.plot(indata)
    ax1.grid()
    ax1.axis([0, CHUNK, -5000, 5000])
    fftData = np.abs(np.fft.rfft(indata))  # Max freq es CHUNK
    fftData = fftData[:fftData.shape[0]//2+1]
    fftTime = np.fft.rfftfreq(CHUNK, 1./RATE)
    # Plot frequency domain graph
    ax2.cla()
    ax2.plot(fftTime, fftData)
    ax2.grid()
    ax2.axis([0, 6000, 0, 10**6])
    nBars = 10
    splitIndex = wantedF2Index(fftTime)
    splitedFFT = np.split(fftData, splitIndex)
    MAX_Amp = 1e5
    avgFFT = np.array([np.max(i) for i in splitedFFT[1:]])
    ax3.cla()
    ax3.bar([i for i in range(int(nBars))], avgFFT/MAX_Amp)
    ax3.grid()
    ax3.axis([0, nBars, 0, 15])
    ax4.cla()
    ax4.bar([i for i in range(int(nBars))], [ampTuned(x) for x in avgFFT])
    ax4.grid()
    ax4.axis([0, nBars, 0, 12])

    plt.pause(0.0001)
    print("took %.02f ms" % ((time.time()-t1)*1000))


if __name__ == "__main__":
    with pyaudio.PyAudio() as p:
        """
        Create PyAudio instance via context manager.
        Spinner is a helper class, for `pretty` output
        """
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

        print(
            f"Recording from: ({default_speakers['index']}){default_speakers['name']}")

        CHANNELS = default_speakers["maxInputChannels"]
        RATE = int(default_speakers["defaultSampleRate"])
        frames_per_buffer = pyaudio.get_sample_size(pyaudio.paInt16)
        READ_FREQUENCY = 10
        CHUNK = RATE // READ_FREQUENCY  # RATE / number of updates per second
        RECORD_SECONDS = 5
        print(READ_FREQUENCY, frames_per_buffer)

        stream = p.open(format=pyaudio.paInt16, channels=CHANNELS, rate=RATE, input=True,
                        frames_per_buffer=CHUNK, input_device_index=default_speakers["index"])

        plt.ion()
        fig = plt.figure(figsize=(10, 8))
        ax1 = fig.add_subplot(411)
        ax2 = fig.add_subplot(412)
        ax3 = fig.add_subplot(413)
        ax4 = fig.add_subplot(414)

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            data = stream.read(CHUNK)
            a = Thread(target=soundPlot, args=(
                data, ax1, ax2, ax3, ax4,  CHUNK, RATE,))
            a.run()

        stream.stop_stream()
        stream.close()
        p.terminate()
