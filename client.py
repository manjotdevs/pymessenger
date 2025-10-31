#!/usr/bin/env python3
import queue
import socket
import threading
import tkinter as tk
from datetime import datetime
from tkinter import simpledialog, messagebox, scrolledtext


def now_time():
    return datetime.now().strftime("%H:%M")


class ChatClient:
    def __init__(self, master):
        self.master = master
        self.sock = None
        self.recv_queue = queue.Queue()

        master.title("PYMessenger - WhatsApp Light Style")
        master.geometry("550x550")
        master.configure(bg="#ECE5DD")

        # Ask for connection details
        self.server_ip = simpledialog.askstring("Server IP", "Enter server IP:", parent=master)
        if not self.server_ip:
            messagebox.showerror("Error", "Server IP required!")
            master.destroy()
            return

        self.server_port = 7070
        self.username = simpledialog.askstring("Username", "Enter your username:", parent=master)
        if not self.username:
            messagebox.showerror("Error", "Username required!")
            master.destroy()
            return

        # Chat display area
        self.chat_frame = tk.Frame(master, bg="#ECE5DD")
        self.chat_frame.pack(fill="both", expand=True, padx=10, pady=10)

        self.canvas = tk.Canvas(self.chat_frame, bg="#ECE5DD", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.chat_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#ECE5DD")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # Message input area
        self.entry_frame = tk.Frame(master, bg="#FFFFFF", relief="solid", bd=1)
        self.entry_frame.pack(fill="x", padx=10, pady=10)

        self.entry = tk.Entry(self.entry_frame, font=("Segoe UI", 11), bg="#FFFFFF", relief="flat")
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 5), pady=5)
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = tk.Button(
            self.entry_frame, text="Send", command=self.send_message,
            bg="#128C7E", fg="white", relief="flat", font=("Segoe UI", 10, "bold"), padx=12, pady=5
        )
        self.send_btn.pack(side="right", padx=(5, 10), pady=5)

        # Connect to server
        if not self.connect():
            messagebox.showerror("Connection Failed", f"Could not connect to {self.server_ip}:{self.server_port}")
            master.destroy()
            return

        threading.Thread(target=self.recv_loop, daemon=True).start()
        self.master.after(100, self.process_incoming)

    # Connect to server
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, self.server_port))
            self.sock.sendall((self.username + "\n").encode("utf-8"))
            return True
        except Exception as e:
            print("Connection error:", e)
            return False

    # Background receiving
    def recv_loop(self):
        try:
            while True:
                data = self.sock.recv(4096)
                if not data:
                    break
                text = data.decode("utf-8").strip()
                for line in text.splitlines():
                    self.recv_queue.put(line)
        except Exception:
            self.recv_queue.put("** Disconnected from server **")

    # Process received messages
    def process_incoming(self):
        while not self.recv_queue.empty():
            msg = self.recv_queue.get()
            self.display_message(msg)
        self.master.after(100, self.process_incoming)

    # Display message bubbles (WhatsApp style)
    def display_message(self, msg):
        if msg.startswith("SERVER"):
            return  # ignore system messages

        # Expected format: username [time]: text
        try:
            name_part, text = msg.split(":", 1)
            username = name_part.split("[")[0].strip()
            time_part = name_part.split("[")[1].replace("]", "").strip()
            text = text.strip()
        except Exception:
            username = "Unknown"
            time_part = now_time()
            text = msg.strip()

        is_self = (username == self.username)

        frame = tk.Frame(self.scrollable_frame, bg="#ECE5DD")

        if is_self:
            bubble = tk.Label(
                frame, text=text, bg="#DCF8C6", fg="black",
                font=("Segoe UI", 11), wraplength=300, justify="left",
                anchor="e", padx=10, pady=6, bd=0
            )
            bubble.pack(anchor="e", padx=10, pady=4)
        else:
            # Create avatar (circle with initial)
            avatar = tk.Canvas(frame, width=30, height=30, bg="#ECE5DD", highlightthickness=0)
            avatar.create_oval(2, 2, 28, 28, fill="#34B7F1", outline="")
            avatar.create_text(15, 15, text=username[0].upper(), fill="white", font=("Segoe UI", 10, "bold"))
            avatar.pack(side="left", padx=(5, 5))

            bubble = tk.Label(
                frame, text=text, bg="#FFFFFF", fg="black",
                font=("Segoe UI", 11), wraplength=300, justify="left",
                anchor="w", padx=10, pady=6, bd=0
            )
            bubble.pack(side="left", padx=5, pady=4)

        frame.pack(fill="x", anchor="w" if not is_self else "e")
        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1)

    # Send message
    def send_message(self):
        text = self.entry.get().strip()
        if not text:
            return
        try:
            self.sock.sendall((text + "\n").encode("utf-8"))
            self.entry.delete(0, "end")
        except Exception as e:
            messagebox.showerror("Error", f"Send failed: {e}")
            self.sock.close()


def on_close(root, client):
    try:
        if client.sock:
            client.sock.close()
    except:
        pass
    root.destroy()


if __name__ == "__main__":
    root = tk.Tk()
    client = ChatClient(root)
    root.protocol("WM_DELETE_WINDOW", lambda: on_close(root, client))
    root.mainloop()
