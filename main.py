from flask import Flask, render_template, request, redirect, url_for
import socket
import json
from datetime import datetime
import os
import threading
import tempfile


app = Flask(__name__)   

@app.route('/')
def index():
    ensure_storage()
    data_path = "storage/data.json"
    with open(data_path, "r", encoding="utf-8") as f:
        messages = json.load(f)
    return render_template('index.html', messages=messages)

@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html'), 404

def send_udp_message(payload, host="127.0.0.1", port=5000):
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    sock.sendto(data, (host, port))
    sock.close()

def ensure_storage():
    os.makedirs("storage", exist_ok=True)
    data_path = os.path.join("storage", "data.json")
    if not os.path.exists(data_path):
        with open(data_path, "w", encoding="utf-8") as f:
            json.dump({}, f, ensure_ascii=False, indent=2)

def udp_server(host="0.0.0.0", port=5000):
    ensure_storage()
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((host, port))
    data_path = "storage/data.json"

    while True:
        data, addr = sock.recvfrom(65535)  
        try:
            text = data.decode("utf-8")
            message = json.loads(text)  
            timestamp = datetime.now().isoformat(sep=' ')
            
            
            with open(data_path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            
            existing[timestamp] = message

            
            fd, tmpname = tempfile.mkstemp(dir="storage")
            with os.fdopen(fd, "w", encoding="utf-8") as tmpf:
                json.dump(existing, tmpf, ensure_ascii=False, indent=2)
            os.replace(tmpname, data_path)
        except Exception as e:
            print("Ошибка UDP-сервера:", e)


@app.route('/message', methods=['GET', 'POST'])
def message():
    if request.method == 'GET':
        return render_template('message.html')
    
    
    username = request.form.get('username', '').strip()
    message_text = request.form.get('message', '').strip()

    if not username or not message_text:
        return render_template('message.html', error='Заполните все поля')
    
    
    payload = {"username": username, "message": message_text}
    
    send_udp_message(payload)
    
    return redirect(url_for('index'))


if __name__ == '__main__':
    ensure_storage()
    t = threading.Thread(target=udp_server, daemon=True)
    t.start()
    app.run(host='0.0.0.0', port=3000)


