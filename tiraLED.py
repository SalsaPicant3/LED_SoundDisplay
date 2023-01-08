import machine
import time
import ustruct
import sys
import asyncio 
import queue


T0H = 0.4e-6  # sec
T1H = 0.8e-6  # sec
T0L = 0.85e-6 # sec
T1L = 0.45e-6 # sec
RES = 50e-6 #sec


class LED_Strip:
    def __init__(self, port, LED_NUM, refreshRate) -> None:
        self.stop = asyncio.Event()
        self.refreshRate = refreshRate
        self.lock = asyncio.Lock()
        self.ledData = [(0,0,0) for _ in range(LED_NUM)] 
        self.queue = asyncio.Queue(LED_NUM)
        self.WS2812B = WS2812B(port, self.lock, self.ledData)
        
        
    
    async def run(self):
        self.end.acquire()
        dequeue = asyncio.create_task(self.__dequeue())
        updateLedTime = max(T0H + T0L, T1H + T1L) * len(self.ledData) + RES
        refreshPeriode = max(1/self.refreshRate, updateLedTime)
        update_io = asyncio.create_task(self.WS2812B.update(), refreshPeriode - updateLedTime)
        
        await self.stop.wait()
        
        dequeue.terminate()
        update_io.terminate()
        
        self.stop.clear()
        
        
        
    def stop(self):
        self.stop.set()
    
    def enQueue(self, data):
        
        
    
    async def __dequeue(self):
        while not self.end:
            await self.lock.release()
            while not self.queue.empty():
                index, data = self.queue.get()
                self.ledData[index] = data
            await self.lock.acquire()
        
        
class WS2812B:
    def __init__(self, port, lock, dataLED) -> None:
        self.port = port
        self.locl = lock
        self.dataLED = dataLED
            
    async def __portState(self, state):
        match state:
            case '0':
                self.port.value(1)
                await asyncio.sleep(T0H)
                self.port.value(0)
                await asyncio.sleep(T0L)
            case '1':
                self.port.value(1)
                await asyncio.sleep(T1H)
                self.port.value(0)
                await asyncio.sleep(T1L)
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
        
    async def update(self, refreshRate):
        self.lock.acquire()
        for RGB in self.dataLED:
            R, G, B = RGB
            self.writeByte(G)
            self.writeByte(R)
            self.writeByte(B)
        self.lock.release()
        await asyncio.sleep(refreshRate + RES)
            
                
        
            
    
        
        
        






