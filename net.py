import machine
from machine import *
import network
import socket


class Network:
    def __init__(self, ssid, password):
        self.ssid = ssid
        self.password = password
        self.wlan = network.WLAN(network.STA_IF)
        self.wlan.active(True)
        self.connect()
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        
        self.response = ""
        self.request = ""
        self.conn = ""
        self.addr = ""
    
    def connect(self):
        if not self.wlan.isconnected():
            print('Connecting')
            self.wlan.connect(self.ssid, self.password)
            while not self.wlan.isconnected():
                pass
    
    def create_socket_server(self):
        self.s.bind(('0.0.0.0', 80))
        self.s.listen(5)
        self.s.settimeout(0.5)
        try:
            self.conn, self.addr = self.s.accept()
            print('连接来自:', self.addr)
            self.request = self.conn.recv(1024)
            self.request = str(self.request, 'GB2312')
            print('收到请求:\n', self.request)
            self.response = self.generate_response(self.request)
            self.conn.send(self.response)
            self.conn.close()
        except:
            pass

    def generate_response(self, request):
        return self.response
    