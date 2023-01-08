import machine
import time
import ustruct
import sys
import uasyncio 
import queue


T0H = 0.4e-6  # sec
T1H = 0.8e-6  # sec
T0L = 0.85e-6 # sec
T1L = 0.45e-6 # sec
RES = 50e-6 #sec


class LED_Strip:
    def __init__(self, port, LED_NUM) -> None:
        self.lock = uasyncio.Lock()
        self.ledData = [(0,0,0) for _ in range(LED_NUM)] 
        self.queue = queue.Queue(LED_NUM)
        WS2812B_LS = WS2812B_LED_Strip(port, self.queue, self.lock, self.ledData)
        IO_Manager = WS2812B(port, self.lock, self.ledData)
        
    
    async def main(self):
        uasyncio.create_task(self.__dequeue())
        
    
    async def __dequeue(self):
        await self.lock.release()
        while not self.queue.empty():
            index, data = self.queue.get()
            self.ledData[index] = data
        await self.lock.acquire()
        
        
        


class WS2812B_LED_Strip:
    def __init__(self, port, queue, lock, ledData) -> None:
        self.port = port
        self.queue = queue
        self.lock = lock
        self.__StateLEDs = ledData
        self.Pin = machine.Pin(port, machine.Pin.OUT)

    
    def setRGB_LED(self, NumLED, State):
        #State (R, G, B)
        if NumLED >= len(self.__StateLEDs):
            raise IndexError
        self.queue.put((NumLED, State))
        
    
    def run(self):
        pass
    
    
    def stop(self):
        pass
    

class WS2812B:
    def __init__(self, port, lock, dataLED) -> None:
        self.port = port
        self.locl = lock
        self.dataLED = dataLED
            
    def __portState(self, state):
        match state:
            case '0':
                self.port.value(1)
                time.sleep(T0H)
                self.port.value(0)
                time.sleep(T0L)
            case '1':
                self.port.value(1)
                time.sleep(T1H)
                self.port.value(0)
                time.sleep(T1L)
            case 'RES':
                time.sleep(RES)
            case _:
                raise KeyError
    
    @staticmethod         
    def __number2bin(num, perimtedLength):
        binary = bin(num).replace('0b', '')
        if len(binary) > perimtedLength:
            raise ValueError(f'Expected max length {perimtedLength}, got number {num} -> len {len(num)}')
        return '0' * (perimtedLength - len(binary)) + binary
    
    def writeByte(self, number:int):
        byte = self.__number2bin(number, 8)
        for bit in byte:
            self.__portState(bit)
        
    async def update(self):
        self.lock.acquire()
        for RGB in self.dataLED:
            R, G, B = RGB
            self.writeByte(G)
            self.writeByte(R)
            self.writeByte(B)
        self.lock.release()
        self.__portState('RES')
            
                
        
            
    
        
        
        






