#!/usr/bin/env python3
import socket
import threading

HOST = "0.0.0.0"
PORT = 7070

clients = {}
lock = threading.Lock()


def broadcast(msg):
    """Send message to all connected clients."""
    with lock:
        disconnected = []
        for client in list(clients.keys()):
            try:
                client.sendall(msg.encode("utf-8"))
            except:
                disconnected.append(client)

        for client in disconnected:
            try:
                client.close()
            except:
                pass
            clients.pop(client, None)


def handle_client(sock, addr):
    """Handle communication with a single client."""
    username = None
    try:
        username = sock.recv(1024).decode("utf-8").strip()
        if not username:
            sock.close()
            return

        with lock:
            clients[sock] = username
        print(f"[+] {username} joined from {addr}")

        # Listen for messages
        while True:
            data = sock.recv(4096)
            if not data:
                break
            text = data.decode("utf-8").strip()
            if text:
                full_msg = f"{username}: {text}\n"
                broadcast(full_msg)

    except ConnectionResetError:
        pass
    except Exception as e:
        print(f"[!] Error with {addr}: {e}")
    finally:
        with lock:
            if sock in clients:
                left_user = clients.pop(sock)
                print(f"[-] {left_user} disconnected from {addr}")
        try:
            sock.close()
        except:
            pass


def main():
    """Main server loop."""
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind((HOST, PORT))
    server.listen(10)
    print(f"[SERVER] Listening on {HOST}:{PORT}")

    threads = []

    try:
        while True:
            sock, addr = server.accept()
            thread = threading.Thread(target=handle_client, args=(sock, addr), daemon=True)
            thread.start()
            threads.append(thread)
    except KeyboardInterrupt:
        print("\n[SERVER] Shutting down gracefully...")
    finally:
        with lock:
            for client in list(clients.keys()):
                try:
                    client.close()
                except:
                    pass
            clients.clear()
        server.close()
        print("[SERVER] Closed all connections.")


if __name__ == "__main__":
    main()
