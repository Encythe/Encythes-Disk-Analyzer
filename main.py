import time, argparse, sys
from PyQt6.QtCore import Qt, QTimer, QThread, pyqtSignal
from PyQt6.QtGui import (
    QPixmap,
    QPalette,
    QColor
)
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDial,
    QDoubleSpinBox,
    QLabel,
    QLineEdit,
    QListWidget,
    QMainWindow,
    QSlider,
    QSpinBox,
    QWidget,
    QVBoxLayout,
    QGridLayout,
    QScrollArea
)
import win32api

from constants import *
from functions import *

app = QApplication([])

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
        
        
class StorageMonitor(QWidget):
    def __init__(self, drive_letter):
        super().__init__()
        self.drive_letter = drive_letter
        layout = QVBoxLayout()
        self.setMaximumHeight(200)
        
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(24,30,36))
        self.setPalette(palette)
        self.setAutoFillBackground(True)
        
        self.setLayout(layout)
        layout.setSpacing(4)
        
        Header = h2Text(f"C: \"NULL\"")
        Font = Header.font()
        Font.setItalic(True)
        Header.setFont(Font)
        
        self.header = Header
        layout.addWidget(self.header)
        
        
        self.delta = 0
        self.last_updated = 0
        
        self.io = {"read": 0, "write": 0}
        self.local_history = []
        self.delta_history = []
        
        Usage = Text(f"0 B / 0 B [0.00%]")
        Font = Usage.font()
        Font.setBold(True)
        Font.setPointSize(14)
        Usage.setFont(Font)
        self.usage_label = Usage
        
        self.free_label = Text("0 B FREE")

        self.activity_label = Text("0 B/s")
        self.io_label = Text("I/O: READ 0 B/s | WRITE 0 B/s")
        # self.write_label = Text("Write: 0 B/s")
        
        layout.addWidget(self.usage_label)
        layout.addWidget(self.free_label)
        
        layout.addWidget(self.activity_label)
        layout.addWidget(self.io_label)
        # layout.addWidget(self.write_label)

        self.update_usage()
        self.update_drive()
        self.show()
        
        self.usage_timer = QTimer()
        self.usage_timer.setInterval(int(UNIT*1000))
        self.usage_timer.timeout.connect(self.update_usage)
        self.usage_timer.start()
        
        self.drive_timer = QTimer()
        self.drive_timer.setInterval(5000)
        self.drive_timer.timeout.connect(self.update_drive)
        self.drive_timer.start()
        
    def update_drive(self):
        self.header.setText(f"{self.drive_letter} \"{win32api.GetVolumeInformation(self.drive_letter + '\\')[0].upper()}\"") 
        
    def update_usage(self):
        try:
            usage = get_drive_usage(self.drive_letter)
        except FileNotFoundError as e:
            # This drive was probably disconnected.
            self.setHidden(True)
            return
        LOCAL_HISTORY = self.local_history
        
        LOCAL_HISTORY.insert(0, usage)

        if len(LOCAL_HISTORY) > int(HISTORY):
            LOCAL_HISTORY.pop(HISTORY)
        
        Start = LOCAL_HISTORY[-1]
        End = LOCAL_HISTORY[0]
        
        # if End['perc'] > WARNING:
        #     # Set text color to red
        #     self.usage_label.setStyleSheet(RED)
        # elif End['perc'] > CAUTION:
        #     self.usage_label.setStyleSheet(f"color: rgb(255, {int(255-127*((End['perc']-CAUTION)/(WARNING-CAUTION)))}, 127);")
        #     # print(255-127*((End['perc']-CAUTION)/(WARNING-CAUTION)))
        # elif End['perc'] > NOMINAL:
        #     self.usage_label.setStyleSheet(f"color: rgb({128+int(127*(End['perc']-NOMINAL)/(75-NOMINAL))}, 255, 127);")
        # else:
            # goal: 127, 196, 255
        if End['perc'] <= TERMINAL:
            self.usage_label.setStyleSheet(f"color: hsv({180-(180*End['perc']/TERMINAL)}, {SATURATION}, 100%);")
            self.free_label.setStyleSheet(f"color: hsv({180-(180*End['perc']/TERMINAL)}, {SATURATION}, 100%);")
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(24,30,36))
            self.setPalette(palette)
        else:
            self.usage_label.setStyleSheet(f"color: hsv({360-(90*(End['perc']-TERMINAL)/10)}, {SATURATION}, 100%);")
            self.free_label.setStyleSheet(f"color: hsv({360-(90*(End['perc']-TERMINAL)/10)}, {SATURATION}, 100%);")
            palette = self.palette()
            palette.setColor(QPalette.ColorRole.Window, QColor(48,24,24))
            self.setPalette(palette)
        
        
        self.usage_label.setText(f"{convert_readable(End['used'], show_diff_sign=False)} / {convert_readable(End['total'], show_diff_sign=False)} [{End['perc']:.2f}%]")
        self.free_label.setText(f"{convert_readable(End['free'], show_diff_sign=False)} FREE")
        
        used_diff = End['used'] - Start['used']
        RATE_OF_CHANGE = used_diff / len(LOCAL_HISTORY)

        
        if self.last_updated < time.time() - 1:
            new = get_drive_usage(self.drive_letter)
            io = sample_drive_io(self.drive_letter)
            
            if len(self.delta_history) < 2:
                while len(self.delta_history) < 2:
                    self.delta_history.insert(0, new)
            
            self.delta_history.insert(0, new)
            if len(self.delta_history) > 2:
                self.delta_history.pop()
            
            self.last_updated = time.time()
            self.delta = self.delta_history[0]['used'] - self.delta_history[1]['used']

            self.io_label.setText(f"READ {convert_readable(io['read'], show_diff_sign=False)}/s | WRITE {convert_readable(io['write'], show_diff_sign=False)}/s")

            difference = io['write']-io['read']
            write_heavy = difference >= 0 and True or False
            magnitude = magnitude_bytes(difference)

            if write_heavy:
                self.io_label.setStyleSheet(f"color: rgb(255, {255-51*magnitude}, {255-51*magnitude});")
            else:
                self.io_label.setStyleSheet(f"color: rgb({255-51*magnitude}, {255-51*magnitude}, 255);")


        self.activity_label.setText(f"{convert_readable(self.delta)} [{convert_readable(RATE_OF_CHANGE)}/s]")
        
        if self.delta >= 0:
            self.activity_label.setStyleSheet(f"color: rgb(255, {255-51*magnitude_bytes(self.delta)}, {255-51*magnitude_bytes(self.delta)});")
            # self.free_label.setStyleSheet(f"color: rgb(255, {255-51*magnitude_bytes(self.delta)}, {255-51*magnitude_bytes(self.delta)});")
        else:
            self.activity_label.setStyleSheet(f"color: rgb({255-51*magnitude_bytes(self.delta)}, 255, {255-51*magnitude_bytes(self.delta)});")
            # self.free_label.setStyleSheet(f"color: rgb({255-51*magnitude_bytes(self.delta)}, 255, {255-51*magnitude_bytes(self.delta)});")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(PROGRAM_NAME)
        self.items = []
        self.grid = QGridLayout()
        self.setMaximumHeight(0) # Scale to the lowest possible height as possible
        
        layout = QVBoxLayout()
        HeaderLabel = h1Text(PROGRAM_NAME.upper())
        HeaderLabel.setMaximumHeight(24)
        layout.addWidget(HeaderLabel)
        layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(48,56,64))
        self.setPalette(palette)
        
        index = -1
        for i in DRIVES:
            index += 1
            Vertical = index // 3
            Horizontal = index % 3
            StorageMonitorItem = QVBoxLayout()
            StorageMonitorItemWidget = StorageMonitor(i.upper())
            StorageMonitorItem.addWidget(StorageMonitorItemWidget)
        
            self.grid.addLayout(StorageMonitorItem, Vertical, Horizontal)
            self.items.append(StorageMonitorItemWidget)
        
        layout.addLayout(self.grid)
        
        widget = QWidget()
        widget.setLayout(layout)
        
        scroll_area = QScrollArea()
        scroll_area.setWidget(widget)
        scroll_area.setWidgetResizable(True)
        
        self.setCentralWidget(widget)
        
        self.timer = QTimer()
        self.timer.setInterval(int(1000))
        self.timer.timeout.connect(self.rescan_drives)
        self.timer.start()
        
    def rebuild_grid(self):
        width = self.width()
        # self.resize(width, 0)
        column_width = 350 
        cols = max(1, width // column_width)

        for i, widget in enumerate(self.items):
            row = i // cols
            col = i % cols
            self.grid.addWidget(widget, row, col)

    def resizeEvent(self, event):
        self.rebuild_grid()
        return super().resizeEvent(event)

    def rescan_drives(self):
        existing_drives = set(widget.drive_letter for widget in self.items)
        DRIVES = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
        current_drives = set(DRIVES)

        # Add new drives
        for drive in current_drives - existing_drives:
            new_widget = StorageMonitor(drive)
            self.items.append(new_widget)
            self.rebuild_grid()

        # Remove disconnected drives
        for widget in self.items[:]:
            if widget.drive_letter not in current_drives:
                self.items.remove(widget)
                widget.setParent(None)
                self.rebuild_grid()
        

class Color(QWidget):
    def __init__(self, color):
        super().__init__()
        self.setAutoFillBackground(True)

        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor(color))
        self.setPalette(palette)

window = MainWindow()
window.show()
app.exec()

