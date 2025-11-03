#!/usr/bin/env python3
import socket
import threading

HOST = "0.0.0.0"
PORT = 7070

clients = {}  


def broadcast(msg, sender_sock=None):
    """Send message to all clients except the sender."""
    for client in list(clients.keys()):
        if client is not sender_sock:
            try:
                client.sendall(msg)
            except Exception:
                client.close()
                del clients[client]


def handle_client(conn, addr):
    """Handle messages from a single client."""
    try:
        username = conn.recv(1024).decode().strip()
        clients[conn] = username
        print(f"[+] {username} joined from {addr}")
        broadcast(f"{username} joined the chat!".encode(), conn)

        while True:
            data = conn.recv(4096)
            if not data:
                break
            broadcast(data, conn)

    except Exception as e:
        print(f"[!] Error with {addr}: {e}")
    finally:
        user = clients.get(conn, "Unknown")
        print(f"[-] {user} disconnected")
        broadcast(f"{user} left the chat.".encode(), conn)
        if conn in clients:
            del clients[conn]
        conn.close()


def main():
    print(f"Server started on {HOST}:{PORT}")
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind((HOST, PORT))
    server.listen()

    try:
        while True:
            conn, addr = server.accept()
            threading.Thread(target=handle_client, args=(conn, addr), daemon=True).start()
    except KeyboardInterrupt:
        print("\nServer shutting down...")
    finally:
        server.close()


if __name__ == "__main__":
    main()
