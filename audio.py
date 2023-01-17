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


def soundPlot(stream, ax1, ax2, ax3, CHUNK, RATE):
    t1 = time.time()
    data = stream.read(CHUNK)
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
    print(fftTime[-1])
    # Plot frequency domain graph
    ax2.cla()
    ax2.plot(fftTime, fftData)
    ax2.grid()
    ax2.axis([0, 6000, 0, 10**6])
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
        ax1 = fig.add_subplot(311)
        ax2 = fig.add_subplot(312)
        ax3 = fig.add_subplot(313)

        for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
            soundPlot(stream, ax1, ax2, ax3,  CHUNK, RATE)

        stream.stop_stream()
        stream.close()
        p.terminate()
