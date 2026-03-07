import time, psutil
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QPalette, QColor
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QScrollArea
)

from constants import *  # HEADER_FONT, FONT, PROGRAM_NAME, UNIT, HISTORY, SATURATION
from functions import get_drive_usage, sample_drive_io, convert_readable, magnitude_bytes

# -------------------
# GUI Text Widgets
class h1Text(QLabel):
    def __init__(self, text):
        super().__init__(text)
        font = self.font()
        font.setPointSize(20)
        font.setFamily(HEADER_FONT)
        font.setBold(True)
        font.setItalic(True)
        self.setFont(font)
        self.setWordWrap(False)

class h2Text(QLabel):
    def __init__(self, text):
        super().__init__(text)
        font = self.font()
        font.setPointSize(16)
        font.setFamily(HEADER_FONT)
        font.setBold(True)
        self.setFont(font)
        self.setWordWrap(False)

class Text(QLabel):
    def __init__(self, text):
        super().__init__(text)
        font = self.font()
        font.setPointSize(12)
        font.setFamily(FONT)
        self.setFont(font)
        self.setWordWrap(False)

# -------------------
# Storage Monitor
class StorageMonitor(QWidget):
    def __init__(self, mountpoint):
        super().__init__()
        self.mountpoint = mountpoint
        layout = QVBoxLayout()
        self.setMaximumHeight(200)
        self.setLayout(layout)
        layout.setSpacing(4)

        # Palette background
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(24,30,36))
        self.setPalette(palette)
        self.setAutoFillBackground(True)

        # Header with mountpoint
        part = next((p for p in psutil.disk_partitions(all=False) if p.mountpoint == mountpoint), None)
        fs_type = part.fstype if part else "UNKNOWN"
        self.header = h2Text(f"{mountpoint} \"{fs_type}\"")
        font = self.header.font()
        font.setItalic(True)
        self.header.setFont(font)
        layout.addWidget(self.header)

        # Labels
        self.usage_label = Text("0 B / 0 B [0.00%]")
        font = self.usage_label.font()
        font.setBold(True)
        font.setPointSize(14)
        self.usage_label.setFont(font)

        self.free_label = Text("0 B FREE")
        self.activity_label = Text("0 B/s")
        self.io_label = Text("I/O: READ 0 B/s | WRITE 0 B/s")

        layout.addWidget(self.usage_label)
        layout.addWidget(self.free_label)
        layout.addWidget(self.activity_label)
        layout.addWidget(self.io_label)

        # History tracking
        self.local_history = []
        self.delta_history = []
        self.delta = 0
        self.last_updated = 0

        # Timer
        self.usage_timer = QTimer()
        self.usage_timer.setInterval(int(UNIT*1000))
        self.usage_timer.timeout.connect(self.update_usage)
        self.usage_timer.start()

        self.update_usage()
        self.show()

    def update_usage(self):
        try:
            usage = get_drive_usage(self.mountpoint)
        except FileNotFoundError:
            self.setHidden(True)
            return

        self.local_history.insert(0, usage)
        if len(self.local_history) > HISTORY:
            self.local_history.pop()
        start = self.local_history[-1]
        end = self.local_history[0]

        # Update labels
        self.usage_label.setText(f"{convert_readable(end['used'])} / {convert_readable(end['total'])} [{end['perc']:.2f}%]")
        self.free_label.setText(f"{convert_readable(end['free'])} FREE")

        used_diff = end['used'] - start['used']
        rate_of_change = used_diff / max(len(self.local_history), 1)
        self.delta = used_diff

        io = sample_drive_io(self.mountpoint)
        self.io_label.setText(f"READ {convert_readable(io['read'])}/s | WRITE {convert_readable(io['write'])}/s")
        self.activity_label.setText(f"{convert_readable(self.delta)} [{convert_readable(rate_of_change)}/s]")

        # Color based on usage percent
        if end['perc'] <= 90:  # TERMINAL usage from constants can replace 90
            hue = 180 - (180 * end['perc'] / 90)
            self.usage_label.setStyleSheet(f"color: hsv({hue}, {SATURATION}, 100%);")
            self.free_label.setStyleSheet(f"color: hsv({hue}, {SATURATION}, 100%);")
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(24,30,36))
            self.setPalette(palette)
        else:
            hue = 360 - (90*(end['perc']-90)/10)
            self.usage_label.setStyleSheet(f"color: hsv({hue}, {SATURATION}, 100%);")
            self.free_label.setStyleSheet(f"color: hsv({hue}, {SATURATION}, 100%);")
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(48,24,24))
            self.setPalette(palette)

# -------------------
# Main Window
class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(PROGRAM_NAME)
        self.items = []
        self.grid = QGridLayout()

        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        header_label = h1Text(PROGRAM_NAME.upper())
        header_label.setMaximumHeight(24)
        layout.addWidget(header_label)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(48,56,64))
        self.setPalette(palette)

        # Mount points
        partitions = [p.mountpoint for p in psutil.disk_partitions(all=False)]
        for index, mount in enumerate(partitions):
            monitor = StorageMonitor(mount)
            self.items.append(monitor)
            row = index // 3
            col = index % 3
            self.grid.addWidget(monitor, row, col)

        layout.addLayout(self.grid)
        container = QWidget()
        container.setLayout(layout)

        scroll = QScrollArea()
        scroll.setWidget(container)
        scroll.setWidgetResizable(True)
        self.setCentralWidget(container)

        # Refresh timer
        self.timer = QTimer()
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self.update_monitors)
        self.timer.start()

    def update_monitors(self):
        partitions = [p.mountpoint for p in psutil.disk_partitions(all=False)]
        current_mounts = set(partitions)
        existing_mounts = set(mon.mountpoint for mon in self.items)

        # Add new mount points
        for mount in current_mounts - existing_mounts:
            monitor = StorageMonitor(mount)
            self.items.append(monitor)
            row = len(self.items) // 3
            col = len(self.items) % 3
            self.grid.addWidget(monitor, row, col)

        # Remove removed mount points
        for mon in self.items[:]:
            if mon.mountpoint not in current_mounts:
                self.items.remove(mon)
                mon.setParent(None)

# -------------------
app = QApplication([])
window = MainWindow()
window.show()
app.exec()