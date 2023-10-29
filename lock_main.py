from machine import Pin, UART
import network
import socket
import ujson

lock = Pin(15, Pin.OUT)
lock.value(0)


def add_entry(json_file, key, value):
    try:
        with open(json_file, 'r') as file:
            data = ujson.load(file)
    except:
        data = {}
    data[key] = value
    with open(json_file, 'w') as file:
        ujson.dump(data, file)


def update_entry(json_file, key, new_value):
    try:
        with open(json_file, 'r') as file:
            data = ujson.load(file)
    except:
        print("JSON文件不存在或无法读取")
        return None
    
    if key in data:
        data[key] = new_value
        
        with open(json_file, 'w') as file:
            ujson.dump(data, file)
    else:
        print("Key不存在")


def read_entry(json_file, key):
    try:
        with open(json_file, 'r') as file:
            data = ujson.load(file)
    except:
        print("JSON文件不存在或无法读取")
        return None
    
    if key in data:
        return data[key]
    else:
        print("Key不存在")
        return None


def delete_entry(json_file, key):
    try:
        with open(json_file, 'r') as file:
            data = ujson.load(file)
    except:
        print("JSON文件不存在或无法读取")
        return None
    
    if key in data:
        del data[key]
        
        with open(json_file, 'w') as file:
            ujson.dump(data, file)
    else:
        print("Key不存在")


class Player:
    def __init__(self):
        self.uart = UART(1, 9600, tx=26, rx=27)
    
    def volume_set(self, volume):
        self.uart.write(b'AF:31')
    
    def play_music(self, music):
        self.music_name = read_entry('music.json', 'music')
        if self.music_name is not None:
            self.uart.write(b'A7:' + self.music_name)
        else:
            print('音乐名称有误')

class Server:
    def __init__(self):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.wlan = network.WLAN(network.STA_IF)
        if not self.wlan.active():
            self.wlan.active(True)
    
    def do_connect(self):
        if not self.wlan.isconnected():
            print('connecting to network...')
            self.wlan.connect('Tenda_04F7D0', '123456789')
            while not self.wlan.isconnected():
                pass
        print('network config:', self.wlan.ifconfig())
    
    def creat_server(self):
        if not self.wlan.isconnected():
            self.do_connect()
        else:
            try:
                self.s.bind((self.wlan.ifconfig()[0], 80))
                self.s.listen(1)
            except OSError:
                self.s.close()
                self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                self.s.bind((self.wlan.ifconfig()[0], 80))
                self.s.listen(1)
            finally:
                print('Successfully creat socket server!')
                
    
        
