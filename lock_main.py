from machine import Pin, UART
import network
import socket
import ujson

lock = Pin(15, Pin.OUT)
lock.value(0)


class UserDatabase:
    def __init__(self, file_name):
        self.file_name = file_name
        try:
            with open(file_name, 'r') as f:
                self.data = ujson.load(f)
        except (OSError, ValueError):
            self.data = {}
    
    def save(self):
        with open(self.file_name, 'w') as f:
            ujson.dump(self.data, f)
    
    def get_file(self):
        return self.data
    
    def add_user(self, username, data):
        if username not in self.data:
            self.data[username] = data
            self.save()
            return True
        else:
            return False
    
    def get_user(self, username):
        return self.data.get(username, None)
    
    def update_user(self, username, updated_data):
        if username in self.data:
            user_data = self.data[username]
            user_data.update(updated_data)  # 更新用户数据
            self.save()
            return True
        else:
            return False
    
    def delete_user(self, username):
        if username in self.data:
            del self.data[username]
            self.save()
            return True
        else:
            return False


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
        self.html_response = None
        self.password = None
        self.content_length = None
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
                # 返回输入密码界面
                self.html_response = '''
                                    <html>
                                    <body>
                                        <h1>欢迎使用</h1>
                                        <form method="POST" action="/pwd">
                                            <label >423电子门锁</label>
                                            <input type="number" id="password" name="password" pattern="[0-9]{6}" required><br><br>
                                            <input type="submit" value="Submit">
                                        </form>
                                        <br>
                                    </body>
                                    </html>
                                    '''
                conn.send(self.html_response)
                conn.close()
            
            elif self.request_method == 'POST':
                self.content_length = 0
                if self.request_path == '/pwd':
                    for line in self.request_lines:
                        if 'Content-Length' in line:
                            self.content_length = int(line.split(': ')[1])
                            break
                    if self.content_length > 0:
                        self.password = self.request_lines[-1].split('=')[1]
                        # 在这里你可以处理表单数据，如提取密码等
                        print('Form data:', self.password)
                    
                    # 返回响应给浏览器
                    self.html_response = '''HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
                                        <html>
                                        <body>
                                        <h1>请在提示音后拉门把手!</h1>
                                        </body>
                                        </html>
                                        '''
                    conn.send(self.html_response)
                    conn.close()
    
    def server_loop(self):
        conn, addr = self.s.accept()
        request_data = conn.recv(1024).decode('utf-8')
        self.handle_request(conn, request_data)


if __name__ == '__main__':
    Server_class = Server()
    print('你好')
    # while True:
    #     Server_class.server_loop()
