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
        self.music_name = None
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
        self.request_path = None
        self.request_method = None
        self.request_parts = None
        
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except OSError:
            pass
        self.wlan = network.WLAN(network.STA_IF)
        
        self.request_lines = ''
        self.request_line = []
        
        if not self.wlan.active():
            self.wlan.active(True)
        
        self.do_connect()
        self.creat_server()
    
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
    
    def handle_request(self, conn, request):
        self.request_lines = request.split('\r\n')
        # print('Request line' + str(self.request_lines))
        
        if len(self.request_lines) > 0:
            self.request_line = self.request_lines[0]
            self.request_parts = self.request_line.split(' ')
        
        if len(self.request_parts) == 3:
            self.request_method = self.request_parts[0]
            print('Request method' + str(self.request_method))
            self.request_path = self.request_parts[1]
            print('Request path' + str(self.request_path))
            
            if self.request_method == 'GET' and self.request_path == '/password':
                # 返回HTML界面
                html_response = '''
                                <html>
                <body>
                    <h1>Control Panel</h1>
                    <form method="POST" action="/">
                        <label for="distance">423电子门锁</label>
                        <input type="number" id="password" name="password" pattern="[0-9]{6}" required><br><br>
                        <input type="submit" value="Submit">
                    </form>
                    <br>
                </body>
                </html>
                '''
                conn.send(html_response)
            
            elif self.request_method == 'POST' and self.request_path == '/':
                # 处理表单提交
                content_length = 0
                for line in self.request_lines:
                    if 'Content-Length' in line:
                        content_length = int(line.split(': ')[1])
                        print(content_length)
                        break
                
                if content_length > 0:
                    form_data = self.request_lines[-1]
                    # 在这里你可以处理表单数据，如提取密码等
                    print('Form data:', form_data)
                
                # 返回响应给浏览器
                response = '''HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
                                    <!-- 响应内容 -->
                                    '''
                conn.send(response)
                conn.close()
    
    def server_loop(self):
        conn, addr = self.s.accept()
        request_data = conn.recv(1024).decode('utf-8')
        self.handle_request(conn, request_data)


if __name__ == '__main__':
    Server_class = Server()
    while True:
        Server_class.server_loop()
