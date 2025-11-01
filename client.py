#!/usr/bin/env python3
import socket
import threading
import sys
from PyQt6.QtCore import Qt, pyqtSignal, QThread
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QLineEdit, QPushButton,
    QScrollArea, QLabel, QHBoxLayout, QMessageBox, QInputDialog, QFrame
)
from PyQt6.QtGui import QFont

SERVER_PORT = 7070


# Thread for receiving messages
class ReceiverThread(QThread):
    message_received = pyqtSignal(str)

    def __init__(self, sock):
        super().__init__()
        self.sock = sock
        self.running = True

    def run(self):
        while self.running:
            try:
                msg = self.sock.recv(4096)
                if not msg:
                    break
                self.message_received.emit(msg.decode())
            except Exception:
                break

    def stop(self):
        self.running = False
        try:
            self.sock.close()
        except Exception:
            pass


class ChatClient(QWidget):
    def __init__(self):
        super().__init__()
        self.sock = None
        self.receiver = None
        self.username = None
        self.dark_mode = True
        self.colors = {}

        # --- Initialize UI ---
        self.setup_ui()
        self.apply_theme()

        # --- Show GUI before connecting ---
        self.show()
        QApplication.processEvents()

        self.connect_to_server()

    # ---------- UI SETUP ----------
    def setup_ui(self):
        self.setWindowTitle("PyQt Messenger")
        self.setGeometry(400, 100, 600, 700)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setSpacing(10)
        self.main_layout.setContentsMargins(10, 10, 10, 10)

        # Header
        header_layout = QHBoxLayout()
        self.title = QLabel("Messenger")
        self.title.setFont(QFont("Segoe UI", 20, QFont.Weight.Bold))
        self.toggle_btn = QPushButton("🌙")
        self.toggle_btn.setFixedWidth(60)
        self.toggle_btn.clicked.connect(self.toggle_theme)
        header_layout.addWidget(self.title)
        header_layout.addStretch()
        header_layout.addWidget(self.toggle_btn)
        self.main_layout.addLayout(header_layout)

        # Scroll area for messages
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)
        self.scroll_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll.setWidget(self.scroll_content)
        self.main_layout.addWidget(self.scroll)

        # Input area
        input_layout = QHBoxLayout()
        self.msg_entry = QLineEdit()
        self.msg_entry.setPlaceholderText("Type a message...")
        self.msg_entry.setFont(QFont("Segoe UI", 14))
        self.msg_entry.returnPressed.connect(self.send_message)

        self.send_btn = QPushButton("Send")
        self.send_btn.setFont(QFont("Segoe UI", 14, QFont.Weight.Bold))
        self.send_btn.clicked.connect(self.send_message)

        input_layout.addWidget(self.msg_entry)
        input_layout.addWidget(self.send_btn)
        self.main_layout.addLayout(input_layout)

    # ---------- THEME ----------
    def apply_theme(self):
        if self.dark_mode:
            bg = "#121212"
            text = "#FFFFFF"
            bubble_self = "#00C853"
            bubble_other = "#2E2E2E"
            avatar_bg = "#444"
        else:
            bg = "#F5F5F5"
            text = "#111"
            bubble_self = "#A5D6A7"
            bubble_other = "#E0E0E0"
            avatar_bg = "#BDBDBD"

        self.setStyleSheet(f"""
            QWidget {{ background-color: {bg}; color: {text}; }}
            QLineEdit {{
                background-color: {'#2A2A2A' if self.dark_mode else '#FFF'};
                color: {text};
                border-radius: 10px;
                padding: 8px;
            }}
            QPushButton {{
                background-color: #00C853;
                color: white;
                border-radius: 10px;
                padding: 8px;
            }}
            QPushButton:hover {{ background-color: #00E676; }}
        """)

        self.scroll_content.setStyleSheet(f"background-color: {bg};")
        self.scroll.setStyleSheet("border: none;")

        self.colors = {
            "bubble_self": bubble_self,
            "bubble_other": bubble_other,
            "avatar_bg": avatar_bg,
            "text": text,
        }

    def toggle_theme(self):
        self.dark_mode = not self.dark_mode
        self.toggle_btn.setText("☀️" if self.dark_mode else "🌙")
        self.apply_theme()

    # ---------- CONNECTION ----------
    def connect_to_server(self):
        host, ok = QInputDialog.getText(self, "Server IP", "Enter server IP (e.g. 127.0.0.1):")
        if not ok or not host.strip():
            QMessageBox.warning(self, "Error", "Server IP is required.")
            return

        username, ok = QInputDialog.getText(self, "Username", "Enter your username:")
        if not ok or not username.strip():
            QMessageBox.warning(self, "Error", "Username is required.")
            return

        self.username = username.strip()

        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((host.strip(), SERVER_PORT))
            self.sock.sendall(self.username.encode())
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Connection failed:\n{e}")
            return

        self.receiver = ReceiverThread(self.sock)
        self.receiver.message_received.connect(self.display_message)
        self.receiver.start()

    # ---------- MESSAGE DISPLAY ----------
    def create_message_bubble(self, sender, text):
        """Creates a message bubble aligned by sender type."""
        msg_container = QHBoxLayout()
        msg_container.setContentsMargins(5, 5, 5, 5)

        is_self = sender == self.username

        avatar_label = QLabel()
        avatar_label.setFixedSize(40, 40)
        avatar_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        avatar_label.setText(sender[0].upper())
        avatar_label.setStyleSheet(
            f"border-radius: 20px; background-color: {self.colors['avatar_bg']}; color: white; font-size: 18px;"
        )

        msg_label = QLabel(text)
        msg_label.setWordWrap(True)
        msg_label.setFont(QFont("Segoe UI", 14))
        msg_label.setStyleSheet(f"""
            background-color: {self.colors['bubble_self' if is_self else 'bubble_other']};
            padding: 10px 14px;
            border-radius: 16px;
            color: {self.colors['text']};
        """)

        msg_frame = QFrame()
        msg_layout = QHBoxLayout(msg_frame)
        msg_layout.setContentsMargins(0, 0, 0, 0)

        if is_self:
            msg_layout.addStretch()
            msg_layout.addWidget(msg_label)
        else:
            msg_layout.addWidget(avatar_label)
            msg_layout.addSpacing(8)
            msg_layout.addWidget(msg_label)
            msg_layout.addStretch()

        return msg_frame

    def display_message(self, msg):
        """Display incoming messages in chat area."""
        if ": " in msg:
            sender, text = msg.split(": ", 1)
        else:
            sender, text = "Server", msg

        bubble = self.create_message_bubble(sender, text)
        self.scroll_layout.addWidget(bubble)
        self.scroll.verticalScrollBar().setValue(self.scroll.verticalScrollBar().maximum())

    # ---------- MESSAGE SEND ----------
    def send_message(self):
        text = self.msg_entry.text().strip()
        if not text:
            return
        msg = f"{self.username}: {text}"
        try:
            self.sock.sendall(msg.encode())
        except Exception:
            QMessageBox.warning(self, "Error", "Disconnected from server.")
            return
        self.display_message(msg)
        self.msg_entry.clear()

    # ---------- CLOSE ----------
    def closeEvent(self, event):
        if self.receiver:
            self.receiver.stop()
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ChatClient()
    sys.exit(app.exec())
