import queue
import socket
import threading
import tkinter as tk
from tkinter import simpledialog, messagebox

SERVER_PORT = 7070

class ChatClient:
    def __init__(self, master):
        self.master = master
        self.sock = None
        self.recv_queue = queue.Queue()

        # --- Window setup ---
        master.title("PYMessenger")
        master.geometry("700x600")
        master.configure(bg="#EDEDED")

        # --- Top header ---
        self.header = tk.Frame(master, bg="#075E54", height=55)
        self.header.pack(fill="x", side="top")

        self.header_label = tk.Label(
            self.header,
            text="PYMessenger",
            bg="#075E54",
            fg="white",
            font=("Segoe UI", 14, "bold"),
            pady=10,
            padx=15
        )
        self.header_label.pack(anchor="w")

        # Ask server IP and username
        self.server_ip = simpledialog.askstring("Server IP", "Enter server IP:", parent=master)
        if not self.server_ip:
            messagebox.showerror("Error", "Server IP required!")
            master.destroy()
            return

        self.username = simpledialog.askstring("Username", "Enter your username:", parent=master)
        if not self.username:
            messagebox.showerror("Error", "Username required!")
            master.destroy()
            return

        # --- Chat container ---
        self.chat_frame = tk.Frame(master, bg="#EDEDED")
        self.chat_frame.pack(fill="both", expand=True)

        self.canvas = tk.Canvas(self.chat_frame, bg="#EDEDED", highlightthickness=0)
        self.scrollbar = tk.Scrollbar(self.chat_frame, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg="#EDEDED")

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )
        self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw", width=680)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        # --- Message entry area ---
        self.entry_frame = tk.Frame(master, bg="#F0F0F0")
        self.entry_frame.pack(fill="x", padx=12, pady=10)

        self.entry = tk.Entry(
            self.entry_frame,
            font=("Segoe UI", 11),
            bg="#FFFFFF",
            relief="flat",
            highlightthickness=1,
            highlightbackground="#CCC"
        )
        self.entry.pack(side="left", fill="x", expand=True, padx=(10, 6), pady=10)
        self.entry.bind("<Return>", lambda e: self.send_message())

        self.send_btn = tk.Button(
            self.entry_frame,
            text="Send",
            command=self.send_message,
            bg="#25D366",
            fg="white",
            relief="flat",
            font=("Segoe UI", 10, "bold"),
            padx=14,
            pady=6
        )
        self.send_btn.pack(side="right", padx=(6, 10))

        # --- Connect to server ---
        if not self.connect():
            messagebox.showerror("Connection Failed", f"Could not connect to {self.server_ip}:{SERVER_PORT}")
            master.destroy()
            return

        threading.Thread(target=self.recv_loop, daemon=True).start()
        self.master.after(100, self.process_incoming)

    # --- Socket connection ---
    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.server_ip, SERVER_PORT))
            self.sock.sendall((self.username + "\n").encode("utf-8"))
            return True
        except Exception as e:
            print("Connection error:", e)
            return False

    # --- Receive messages ---
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
            self.recv_queue.put("**Disconnected**")

    def process_incoming(self):
        while not self.recv_queue.empty():
            msg = self.recv_queue.get()
            self.display_message(msg)
        self.master.after(100, self.process_incoming)

    # --- Display messages with alignment ---
    def display_message(self, msg):
        try:
            name_part, text = msg.split(":", 1)
            username = name_part.split("[")[0].strip()
            text = text.strip()
        except:
            username, text = "Unknown", msg.strip()

        is_self = username == self.username

        outer = tk.Frame(self.scrollable_frame, bg="#EDEDED")
        outer.pack(fill="x", pady=5)

        if is_self:
            # Right-aligned message bubble
            inner = tk.Frame(outer, bg="#EDEDED")
            inner.pack(anchor="e", padx=15, fill="x")
            bubble = tk.Label(
                inner,
                text=text,
                bg="#DCF8C6",
                fg="black",
                font=("Segoe UI", 11),
                wraplength=400,
                justify="left",
                anchor="e",
                padx=12,
                pady=8,
                bd=0,
                relief="solid"
            )
            bubble.pack(anchor="e", padx=10)
        else:
            # Left-aligned message bubble with avatar
            inner = tk.Frame(outer, bg="#EDEDED")
            inner.pack(anchor="w", padx=15, fill="x")
            avatar = tk.Canvas(inner, width=38, height=38, bg="#EDEDED", highlightthickness=0)
            avatar.create_oval(2, 2, 36, 36, fill="#34B7F1", outline="")
            avatar.create_text(19, 19, text=username[0].upper(), fill="white", font=("Segoe UI", 11, "bold"))
            avatar.pack(side="left", padx=(0, 5))
            bubble = tk.Label(
                inner,
                text=text,
                bg="#FFFFFF",
                fg="black",
                font=("Segoe UI", 11),
                wraplength=400,
                justify="left",
                anchor="w",
                padx=12,
                pady=8,
                bd=0,
                relief="solid"
            )
            bubble.pack(side="left")

        self.canvas.update_idletasks()
        self.canvas.yview_moveto(1)

    # --- Send message ---
    def send_message(self):
        text = self.entry.get().strip()
        if not text:
            return
        try:
            self.sock.sendall((text + "\n").encode("utf-8"))
            self.entry.delete(0, "end")
        except:
            messagebox.showerror("Error", "Connection lost.")
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
