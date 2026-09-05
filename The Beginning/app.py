import http.server
import socketserver
import threading
import time
import webbrowser
import os

PORT = 5000
DIRECTORY = os.path.dirname(os.path.abspath(__file__))

class Handler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORY, **kwargs)

def start_server():
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🚀 AI English Master đang chạy tại: http://localhost:{PORT}")
        httpd.serve_forever()

if __name__ == "__main__":
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    time.sleep(0.5)

    print(f"Đang mở trình duyệt tại http://localhost:{PORT}...")
    webbrowser.open(f"http://localhost:{PORT}")

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nĐã tắt Server.")