import network
import socket

# 设置ESP32为AP模式
ap = network.WLAN(network.AP_IF)
ap.active(True)
ap.config(essid='MyESP32AP', password='password')

# 创建Socket服务器
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('0.0.0.0', 80))
s.listen(1)

print("Waiting for connection...")


def handle_request(conn, request):
    # 处理HTTP请求
    request_lines = request.split('\r\n')
    
    if len(request_lines) > 0:
        request_line = request_lines[0]
        request_parts = request_line.split(' ')
        
        if len(request_parts) == 3:
            request_method = request_parts[0]
            request_path = request_parts[1]
            
            if request_method == 'GET' and request_path == '/':
                # 返回HTML界面
                html_response = '''HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
                <html>
                <body>
                    <h1>Control Panel</h1>
                    <form method="POST" action="/">
                        <label for="distance">Enter distance:</label>
                        <input type="number" id="distance" name="distance" required><br><br>
                        <input type="submit" value="Submit">
                    </form>
                    <br>
                    <button onclick="start_pushrod()">Start Pushrod</button>
                    <button onclick="start_drill()">Start Drill</button>

                    <script>
                        function start_pushrod() {
                            // 执行启动推杆操作
                            console.log("Pushrod started");
                        }

                        function start_drill() {
                            // 执行启动钻头操作
                            console.log("Drill started");
                        }
                    </script>
                </body>
                </html>
                '''
                
                conn.send(html_response)
            elif request_method == 'POST' and request_path == '/':
                # 处理提交的表单数据
                content_length = 0
                for line in request_lines:
                    if line.startswith('Content-Length:'):
                        content_length = int(line.split(':')[1].strip())
                
                request_data = conn.recv(content_length).decode('utf-8')
                distance = request_data.split('=')[1]
                
                # 将距离输出到REPL
                print("Received distance:", distance)
                
                # 返回响应
                response = '''HTTP/1.1 200 OK\r\nContent-Type: text/html\r\n\r\n
                <html>
                <body>
                    <h1>Distance submitted successfully!</h1>
                </body>
                </html>
                '''
                conn.send(response)
            else:
                # 返回404 Not Found错误
                response = '''HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n
                <html>
                <body>
                    <h1>404 Not Found</h1>
                </body>
                </html>
                '''
                conn.send(response)
        else:
            # 请求行格式不正确
            # 返回400 Bad Request错误
            response = '''HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n
            <html>
            <body>
                <h1>400 Bad Request</h1>
            </body>
            </html>
            '''
            conn.send(response)
    else:
        # 请求数据为空
        # 返回400 Bad Request错误
        response = '''HTTP/1.1 400 Bad Request\r\nContent-Type: text/html\r\n\r\n
        <html>
        <body>
        <h1>400 Bad Request</h1>
        </body>
        </html>
        '''
        conn.send(response)


while True:
    conn, addr = s.accept()
    print("Connected with", addr)
    request_data = conn.recv(1024).decode('utf-8')
    handle_request(conn, request_data)
    conn.close()
