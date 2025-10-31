#!/usr/bin/env python3
import socket
import threading
from datetime import datetime

HOST = "0.0.0.0"  
PORT = 7070

clients_lock = threading.Lock()
clients = {}  # sock -> username


def now_time():
    return datetime.now().strftime("%H:%M")


def broadcast(message, exclude_sock=None):
    data = message.encode("utf-8")
    with clients_lock:
        dead = []
        for sock in clients:
            try:
                sock.sendall(data)
            except Exception:
                dead.append(sock)
        for s in dead:
            remove_client(s)


def remove_client(sock):
    with clients_lock:
        username = clients.pop(sock, None)
    try:
        sock.close()
    except:
        pass
    if username:
        print(f"[-] {username} disconnected.")


def handle_client(conn, addr):
    try:
        raw = conn.recv(2048)
        if not raw:
            conn.close()
            return
        username = raw.decode("utf-8").strip()
        with clients_lock:
            clients[conn] = username
        print(f"[+] {username} connected from {addr[0]}")

        while True:
            data = conn.recv(4096)
            if not data:
                break
            text = data.decode("utf-8").strip()
            if text == "":
                continue
            out = f"{username} [{now_time()}]: {text}\n"
            print(out.strip())
            broadcast(out)
    except Exception as e:
        print("Error:", e)
    finally:
        remove_client(conn)


def main():
    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind((HOST, PORT))
    s.listen(32)
    print(f"💬 Chat server running on {HOST}:{PORT}")

    try:
        while True:
            conn, addr = s.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        with clients_lock:
            for sock in list(clients.keys()):
                try:
                    sock.close()
                except:
                    pass
            clients.clear()
        s.close()


if __name__ == "__main__":
    main()
