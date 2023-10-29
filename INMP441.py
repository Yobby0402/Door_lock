from machine import Pin, I2S
import socket
import network
import micropython

wlan = network.WLAN(network.STA_IF)
if wlan.active():
    wlan.active(True)
    
bck_pin = Pin(25)
ws_pin = Pin(27)
sdin_pin = Pin(26)
audio_in = I2S(0,
               sck=bck_pin, ws=ws_pin, sd=sdin_pin,
               mode=I2S.RX,
               bits=16,
               format=I2S.MONO,
               rate=8000,
               ibuf=8000)


try:
    ibuf = bytearray(8000)
except:
    pass


def connect(ssid='Tenda_04F7D0', password='123456789'):
    print('Connecting')
    wlan.connect(ssid, password)
    while not wlan.isconnected():
        pass


def socket_create():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect(('192.168.1.114', 8001))
    

