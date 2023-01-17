from machine import Pin
import time
l = Pin(6, Pin.OUT)
while True:
    l.toggle()
    time.sleep(1)
