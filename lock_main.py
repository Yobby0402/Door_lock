from machine import Pin, UART
import time
import network
import socket
import ujson
import _thread
from rotary_irq_esp import RotaryIRQ
import os
import ntptime

lock = Pin(15, Pin.OUT)
lock.value(0)

def time_sync():



def write_record_file(record):
    try:
        timestamp = time.time()



class UserDatabase:
    def __init__(self, file_name='Userdata.json'):
        self.file_name = file_name
        try:
            with open(file_name, 'r') as f:
                self.data = ujson.load(f)
        except (OSError, ValueError):
            self.data = {}
    
    def save(self):
        with open(self.file_name, 'w') as f:
            ujson.dump(self.data, f)
    
    def get_data(self):
        return self.data
    
    def add_user(self, username, key, value):
        if username not in self.data:
            self.data[username][key] = value
            self.save()
            return True
        else:
            return False
    
    def get_user(self, username):
        return self.data[username]
    
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
    
    def search_data(self, key, value):
        for sub_dict in self.data:
            if value == self.data[sub_dict][key]:
                return self.data[sub_dict]
        return None


class Player:
    def __init__(self):
        self.music_name = None
        self.uart = UART(1, 9600, tx=26, rx=27)
        self.volume_set()
    
    def volume_set(self, volume=31):
        self.uart.write(b'AF:{}'.format(volume))
    
    def play_music(self, music_name):
        self.uart.write(b'A7:{}'.format(music_name))


class Server:
    def __init__(self):
        self.current_reset_key = None
        self.user_data = None
        self.register_name = None
        self.register_dict = {}
        self.register_content = None
        self.get_data = None
        self.html_response = None
        self.password = None
        self.content_length = None
        self.request_path = None
        self.request_method = None
        self.request_parts = None
        
        self.db = UserDatabase()
        
        self.player = Player()
        
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except OSError:
            pass
        self.wlan = network.WLAN(network.STA_IF)
        
        self.request_lines = ''
        self.request_line = []
        
        if not self.wlan.active():
            self.wlan.active(True)
        
        self.wlan.config(dhcp_hostname='LOCK')
        
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
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((self.wlan.ifconfig()[0], 80))
            self.s.listen(5)
            self.s.settimeout(1)
            print('Successfully creat socket server!')
    
    def search_data(self, key, value):
        for sub_dict in self.all_user_data:
            if value == self.all_user_data[sub_dict][key]:
                return self.all_user_data[sub_dict]
        return None
    
    def handle_request(self, conn, request):
        self.request_lines = request.split('\r\n')
        print('Request line' + str(self.request_lines))
        
        if len(self.request_lines) > 0:
            self.request_line = self.request_lines[0]
            self.request_parts = self.request_line.split(' ')
        
        if len(self.request_parts) == 3:
            self.request_method = self.request_parts[0]
            print('Request method:' + str(self.request_method))
            self.request_path = self.request_parts[1]
            print('Request path:' + str(self.request_path))
            
            if self.request_method == 'GET':
                if self.request_path == '/password':
                    # 返回输入密码界面
                    self.html_response = '''HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                        <!DOCTYPE html>
                                        <html lang="zh">
                                        <head>
                                          <meta name="viewport" content="width=device-width, initial-scale=1">
                                          <style>
                                            body {
                                              display: flex;
                                              flex-direction: column;
                                              align-items: center;
                                              justify-content: center;
                                              height: 100vh;
                                              margin: 0;
                                              background-color: aquamarine;
                                            }
                                        
                                            h1 {
                                              text-align: center;
                                            }
                                        
                                            form {
                                              text-align: center;
                                              max-width: 80%;
                                              padding: 20px;
                                              border: 1px solid #ccc;
                                              border-radius: 5px;
                                              box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
                                              background-color: antiquewhite;
                                            }
                                        
                                            label {
                                              font-size: 18px;
                                            }
                                        
                                            input[type="text"] {
                                              width: 80%;
                                              padding: 10px;
                                              font-size: 16px;
                                              border: 1px solid #ccc;
                                              border-radius: 5px;
                                            }
                                        
                                            input[type="checkbox"] {
                                              width: 20px;
                                              height: 20px;
                                            }
                                        
                                            input[type="submit"] {
                                              width: 80%;
                                              padding: 10px;
                                              font-size: 18px;
                                              background-color: #007bff;
                                              color: #fff;
                                              border: none;
                                              border-radius: 5px;
                                              cursor: pointer;
                                            }
                                        
                                            @media screen and (max-width: 600px) {
                                              form {
                                                max-width: 90%;
                                              }
                                            }
                                          </style>
                                          <title>423门锁</title>
                                        </head>
                                        <body>
                                        <h1>欢迎使用网络钥匙</h1>
                                        <form method="POST" action="/pwd">
                                          <label>请输入密码</label>
                                          <input type="text" id="password" name="password" pattern="[0-9]{6}" required placeholder="六位数字"><br><br>
                                          <input type="checkbox" id="rememberMe" name="play" checked>
                                          <label for="rememberMe">播放开门音效</label><br><br>
                                          <input type="submit" value="提交">
                                        </form>
                                        </body>
                                        </html>
                                        '''
                
                elif self.request_path == '/indoor':
                    self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                        <!DOCTYPE html>
                                        <html>
                                        <head>
                                          <meta name="viewport" content="width=device-width, initial-scale=1">
                                          <style>
                                            body {{
                                              display: flex;
                                              flex-direction: column;
                                              align-items: center;
                                              justify-content: center;
                                              height: 100vh;
                                              margin: 0;
                                              background-color: aquamarine;
                                            }}
                                            h1 {{
                                            text - align: center;
                                              font-size: 24px;
                                            }}
                                            h2 {{
                                            text - align: center;
                                              font-size: 18px;
                                            }}
                                          </style>
                                          <title>欢迎页面</title>
                                        </head>
                                        <body>
                                          <h1>欢迎{}{}</h1>
                                          <h2>请在提示音后拉门把手</h2>
                                        </body>
                                        </html>
                                        """
                    lock.value(1)
                    time.sleep(3)
                    lock.value(0)
                    self.player.play_music('00017')
                
                elif self.request_path == '/reset-password':
                    self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                        <!DOCTYPE html>
                                        <html lang="zh">
                                        <head>
                                          <meta name="viewport" content="width=device-width, initial-scale=1">
                                          <style>
                                            body {
                                              display: flex;
                                              flex-direction: column;
                                              align-items: center;
                                              justify-content: center;
                                              height: 100vh;
                                              margin: 0;
                                              background-color: aquamarine;
                                            }
                                        
                                            h1 {
                                              text-align: center;
                                            }
                                        
                                            form {
                                              text-align: center;
                                              max-width: 80%;
                                              padding: 20px;
                                              border: 1px solid #ccc;
                                              border-radius: 5px;
                                              box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
                                              background-color: antiquewhite;
                                            }
                                        
                                            label {
                                              font-size: 18px;
                                            }
                                        
                                            input[type="text"] {
                                              width: 80%;
                                              padding: 10px;
                                              font-size: 16px;
                                              border: 1px solid #ccc;
                                              border-radius: 5px;
                                            }
                                        
                                            input[type="checkbox"] {
                                              width: 20px;
                                              height: 20px;
                                            }
                                        
                                            input[type="submit"] {
                                              width: 80%;
                                              padding: 10px;
                                              font-size: 18px;
                                              background-color: #007bff;
                                              color: #fff;
                                              border: none;
                                              border-radius: 5px;
                                              cursor: pointer;
                                            }
                                        
                                            @media screen and (max-width: 600px) {
                                              form {
                                                max-width: 90%;
                                              }
                                            }
                                          </style>
                                          <title>423门锁</title>
                                        </head>
                                        <body>
                                        <h1>用户信息修改</h1>
                                        <form method="POST" action="/reset-password">
                                          <label>开锁密码修改</label>
                                          <input type="text" id="JX" name="JX" pattern="[A-Z]*" required placeholder="请输入名称首字母大写"><br><br>
                                          <input type="text" id="old-password" name="old-password" pattern="[0-9]{6}" required placeholder="请输入旧解锁密码(六位数字)"><br><br>
                                          <input type="text" id="password" name="password" pattern="[0-9]{6}" required placeholder="请输入新解锁密码(六位数字)"><br><br>
                                          <input type="submit" value="提交">
                                        </form>
                                        </body>
                                        </html>
                                        """
                
                elif self.request_path == '/reset-code_outdoor':
                    self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                        <!DOCTYPE html>
                                        <html lang="zh">
                                        <head>
                                          <meta name="viewport" content="width=device-width, initial-scale=1">
                                          <style>
                                            body {
                                              display: flex;
                                              flex-direction: column;
                                              align-items: center;
                                              justify-content: center;
                                              height: 100vh;
                                              margin: 0;
                                              background-color: aquamarine;
                                            }

                                            h1 {
                                              text-align: center;
                                            }

                                            form {
                                              text-align: center;
                                              max-width: 80%;
                                              padding: 20px;
                                              border: 1px solid #ccc;
                                              border-radius: 5px;
                                              box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
                                              background-color: antiquewhite;
                                            }

                                            label {
                                              font-size: 18px;
                                            }

                                            input[type="text"] {
                                              width: 80%;
                                              padding: 10px;
                                              font-size: 16px;
                                              border: 1px solid #ccc;
                                              border-radius: 5px;
                                            }

                                            input[type="checkbox"] {
                                              width: 20px;
                                              height: 20px;
                                            }

                                            input[type="submit"] {
                                              width: 80%;
                                              padding: 10px;
                                              font-size: 18px;
                                              background-color: #007bff;
                                              color: #fff;
                                              border: none;
                                              border-radius: 5px;
                                              cursor: pointer;
                                            }

                                            @media screen and (max-width: 600px) {
                                              form {
                                                max-width: 90%;
                                              }
                                            }
                                          </style>
                                          <title>423门锁</title>
                                        </head>
                                        <body>
                                        <h1>用户信息修改</h1>
                                        <form method="POST" action="/reset-code_outdoor">
                                          <label>拨盘密码修改</label>
                                          <input type="text" id="JX" name="JX" pattern="[A-Z]*" required placeholder="请输入名称首字母大写"><br><br>
                                          <input type="text" id="old-code_outdoor" name="old-code_outdoor" pattern="[0-9]{4}" required placeholder="请输入旧拨盘密码(四位数字)"><br><br>
                                          <input type="text" id="code_outdoor" name="code_outdoor" pattern="[0-9]{4}" required placeholder="请输入新拨盘密码(四位数字)"><br><br>
                                          <input type="submit" value="提交">
                                        </form>
                                        </body>
                                        </html>
                                        """
                
                elif self.request_path == '/forget_password':
                    self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                        <!DOCTYPE html>
                                        <html lang="zh">
                                        <head>
                                          <meta name="viewport" content="width=device-width, initial-scale=1">
                                          <style>
                                            body {
                                              display: flex;
                                              flex-direction: column;
                                              align-items: center;
                                              justify-content: center;
                                              height: 100vh;
                                              margin: 0;
                                              background-color: aquamarine;
                                            }

                                            h1 {
                                              text-align: center;
                                            }

                                            form {
                                              text-align: center;
                                              max-width: 80%;
                                              padding: 20px;
                                              border: 1px solid #ccc;
                                              border-radius: 5px;
                                              box-shadow: 0 0 10px rgba(0, 0, 0, 0.2);
                                              background-color: antiquewhite;
                                            }

                                            label {
                                              font-size: 18px;
                                            }

                                            input[type="text"] {
                                              width: 80%;
                                              padding: 10px;
                                              font-size: 16px;
                                              border: 1px solid #ccc;
                                              border-radius: 5px;
                                            }

                                            input[type="checkbox"] {
                                              width: 20px;
                                              height: 20px;
                                            }

                                            input[type="submit"] {
                                              width: 80%;
                                              padding: 10px;
                                              font-size: 18px;
                                              background-color: #007bff;
                                              color: #fff;
                                              border: none;
                                              border-radius: 5px;
                                              cursor: pointer;
                                            }

                                            @media screen and (max-width: 600px) {
                                              form {
                                                max-width: 90%;
                                              }
                                            }
                                          </style>
                                          <title>423门锁</title>
                                        </head>
                                        <body>
                                        <h1>用户信息找回</h1>
                                        <form method="POST" action="/get-password">
                                          <label>找回密码</label>
                                          <input type="text" id="JX" name="JX" pattern="[A-Z]*" required placeholder="请输入名称首字母大写"><br><br>
                                          <input type="text" id="ID" name="ID" required placeholder="请输入身份ID"><br><br>
                                          <input type="submit" value="提交">
                                        </form>
                                        </body>
                                        </html>
                                        """
                try:
                    conn.send(self.html_response)
                except ValueError:
                    pass
                finally:
                    conn.close()
            
            elif self.request_method == 'POST':
                self.content_length = 0
                for line in self.request_lines:
                    if 'Content-Length' in line:
                        self.content_length = int(line.split(': ')[1])
                        break
                
                if self.request_path == '/pwd':
                    if self.content_length > 0:
                        self.password = self.request_lines[-1].split('&')[0].split('=')[1]
                        self.get_data = self.db.search_data('password', self.password)
                        if self.get_data is not None:
                            self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                                <!DOCTYPE html>
                                                <html>
                                                <head>
                                                  <meta name="viewport" content="width=device-width, initial-scale=1">
                                                  <style>
                                                    body {{
                                                      display: flex;
                                                      flex-direction: column;
                                                      align-items: center;
                                                      justify-content: center;
                                                      height: 100vh;
                                                      margin: 0;
                                                      background-color: aquamarine;
                                                    }}
                                                    h1 {{
                                                    text - align: center;
                                                      font-size: 24px;
                                                    }}
                                                    h2 {{
                                                    text - align: center;
                                                      font-size: 18px;
                                                    }}
                                                  </style>
                                                  <title>欢迎页面</title>
                                                </head>
                                                <body>
                                                  <h1>欢迎{}{}</h1>
                                                  <h2>请在提示音后拉门把手</h2>
                                                </body>
                                                </html>
                                                """.format(self.get_data['level'], self.get_data['name'])
                            conn.send(self.html_response)
                            conn.close()
                            if 'on' in self.request_lines[-1]:
                                self.player.play_music(self.get_data['dooring'])
                            lock.value(1)
                            time.sleep(3)
                            lock.value(0)
                        else:
                            self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                                <!DOCTYPE html>
                                                <html>
                                                <head>
                                                  <meta name="viewport" content="width=device-width, initial-scale=1">
                                                  <style>
                                                    body {{
                                                      display: flex;
                                                      flex-direction: column;
                                                      align-items: center;
                                                      justify-content: center;
                                                      height: 100vh;
                                                      margin: 0;
                                                      background-color: aquamarine;
                                                    }}
                                                    h1 {{
                                                    text - align: center;
                                                      font-size: 24px;
                                                    }}
                                                    h2 {{
                                                    text - align: center;
                                                      font-size: 18px;
                                                    }}
                                                  </style>
                                                  <title>错误页面</title>
                                                </head>
                                                <body>
                                                  <h1>您的密码输入有误！</h1>
                                                  <h2>请检查后重新输入！</h2>
                                                </body>
                                                </html>
                                                """
                
                else:
                    self.register_content = self.request_lines[-1]
                    print(self.register_content)
                    self.register_name = self.register_content[
                                         self.register_content.find('=') + 1:self.register_content.find('&')]
                    self.register_dict = eval(
                        '{"' + self.register_content[self.register_content.find('&') + 1:].replace('&',
                                                                                                   '","').replace(
                            '=', '":"') + '"}')
                    print(self.register_dict)
                    self.user_data = self.db.get_user(self.register_name)
                    if 'reset' in self.request_path:
                        self.current_reset_key = self.request_path.split('-')[1]
                        if self.user_data[self.current_reset_key] != self.register_dict[
                            'old-' + self.current_reset_key]:
                            self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                                <!DOCTYPE html>
                                                <html>
                                                <head>
                                                  <meta name="viewport" content="width=device-width, initial-scale=1">
                                                  <style>
                                                    body {{
                                                      display: flex;
                                                      flex-direction: column;
                                                      align-items: center;
                                                      justify-content: center;
                                                      height: 100vh;
                                                      margin: 0;
                                                      background-color: aquamarine;
                                                    }}
                                                    h1 {{
                                                    text - align: center;
                                                      font-size: 24px;
                                                    }}
                                                    h2 {{
                                                    text - align: center;
                                                      font-size: 18px;
                                                    }}
                                                  </style>
                                                  <title>错误页面</title>
                                                </head>
                                                <body>
                                                  <h1>您的密码输入有误！</h1>
                                                  <h2>请检查后重新输入！</h2>
                                                </body>
                                                </html>
                                                """
                        else:
                            self.user_data[self.current_reset_key] = self.register_dict[self.current_reset_key]
                            self.db.update_user(self.register_name, self.user_data)
                            self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                                <!DOCTYPE html>
                                                <html>
                                                <head>
                                                  <meta name="viewport" content="width=device-width, initial-scale=1">
                                                  <style>
                                                    body {{
                                                      display: flex;
                                                      flex-direction: column;
                                                      align-items: center;
                                                      justify-content: center;
                                                      height: 100vh;
                                                      margin: 0;
                                                      background-color: aquamarine;
                                                    }}
                                                    h1 {{
                                                    text - align: center;
                                                      font-size: 24px;
                                                    }}
                                                    h2 {{
                                                    text - align: center;
                                                      font-size: 18px;
                                                    }}
                                                  </style>
                                                  <title>修改页面</title>
                                                </head>
                                                <body>
                                                  <h1>修改密码成功</h1>
                                                </body>
                                                </html>
                                                """
                    
                    elif self.request_path == '/get-password':
                        if self.register_dict['ID'] == self.user_data["ID"]:
                            self.html_response = """HTTP/1.1 200 OK\r\nContent-Type: text/html; charset=utf-8\r\n\r\n
                                                <!DOCTYPE html>
                                                <html>
                                                <head>
                                                  <meta name="viewport" content="width=device-width, initial-scale=1">
                                                  <style>
                                                    body {{
                                                      display: flex;
                                                      flex-direction: column;
                                                      align-items: center;
                                                      justify-content: center;
                                                      height: 100vh;
                                                      margin: 0;
                                                      background-color: aquamarine;
                                                    }}
                                                    h1 {{
                                                    text - align: center;
                                                      font-size: 24px;
                                                    }}
                                                    h2 {{
                                                    text - align: center;
                                                      font-size: 18px;
                                                    }}
                                                  </style>
                                                  <title>密码找回</title>
                                                </head>
                                                <body>
                                                  <h1>欢迎{}{}</h1>
                                                  <h2>您的开锁密码{}</h2>
                                                  <h2>您的拨盘密码{}</h2>
                                                </body>
                                                </html>
                                                """.format(self.user_data['level'],
                                                           self.user_data['name'],
                                                           self.user_data['password'],
                                                           self.user_data['code_outdoor'])
                try:
                    conn.send(self.html_response)
                except ValueError:
                    pass
                finally:
                    conn.close()
    
    def server_loop(self):
        while True:
            try:
                conn, addr = self.s.accept()
                request_data = conn.recv(1024).decode('utf-8')
                self.handle_request(conn, request_data)
            except OSError:
                pass


class RotaryLock:
    def __init__(self):
        self.last_time = None
        self.max_interval_time = 30000
        self.player = Player()
        self.search_result = None
        self._password_char = None
        self.data_base = UserDatabase()
        self.rotary_lock = RotaryIRQ(pin_num_clk=32,
                                     pin_num_dt=33,
                                     min_val=0,
                                     max_val=1,
                                     reverse=False,
                                     range_mode=RotaryIRQ.RANGE_UNBOUNDED)
        
        self.current_direction = None
        self.last_direction = None
        
        self._code_list = []
        self._value_current = None
        
        self.rotary_lock.add_listener(self.code_outdoor_get)
        time.sleep(1)
    
    def code_outdoor_get(self):
        if self.last_time is None:
            self.last_time = time.ticks_ms()
        else:
            if time.ticks_diff(self.last_time, time.ticks_ms()) > self.max_interval_time:
                self.last_direction = None
                self._code_list = []
                self.current_direction = None
        self.last_direction = self.rotary_lock.value()
        self.rotary_lock.reset()
        if self.current_direction == self.last_direction:
            self._value_current += 1
            if self._value_current == 10:
                self._value_current = 0
        else:
            if self.current_direction is not None:
                self._code_list.append(self._value_current)
            self._value_current = 1
            self.current_direction = self.last_direction
        if len(self._code_list) == 4:
            self.password_verification(self._code_list)
            
    def password_verification(self, password):
        self._code_list = []
        self.last_direction = None
        self.current_direction = None
        self._password_char = ''.join(map(str, password))
        self.search_result = self.data_base.search_data("code_outdoor", self._password_char)
        if self.search_result is not None:
            self.player.play_music(self.search_result['dooring'])
            lock.value(1)
            time.sleep(3)
            lock.value(0)
        else:
            self.player.play_music('00099')


if __name__ == '__main__':
    # Server_class = Server()
    Rotary_class = RotaryLock()
    # _thread.start_new_thread(Server_class.server_loop, ())
