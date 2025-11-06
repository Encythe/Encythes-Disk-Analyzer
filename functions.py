import math
from constants import *
import psutil, os, time
import win32.win32pdh as win32pdh

print(DRIVES)

class DriveIO:
    def __init__(self, drive_letter="C:"):
        self.drive = drive_letter
        self.query = win32pdh.OpenQuery()
        path_r = win32pdh.MakeCounterPath((
            None,
            PDH_OBJECT_LOGICALDISK,
            self.drive,
            None,
            0,
            PDH_COUNTER_DISK_READ_BYTES_PER_SEC
        ))
        path_w = win32pdh.MakeCounterPath((
            None,
            PDH_OBJECT_LOGICALDISK,
            self.drive,
            None,
            0,
            PDH_COUNTER_DISK_WRITE_BYTES_PER_SEC
        ))
        self.c_r = win32pdh.AddCounter(self.query, path_r)
        self.c_w = win32pdh.AddCounter(self.query, path_w)

    def sample(self):
        try:
            win32pdh.CollectQueryData(self.query)
            r_val = win32pdh.GetFormattedCounterValue(self.c_r, win32pdh.PDH_FMT_LARGE)[1]
            w_val = win32pdh.GetFormattedCounterValue(self.c_w, win32pdh.PDH_FMT_LARGE)[1]
            return {"read": r_val, "write": w_val}
        except Exception as e:
            return {"read": 0, "write": 0}
    
SAMPLERS: dict[str, DriveIO] = {}    

for drive in DRIVES:
    SAMPLERS[drive] = DriveIO(drive_letter=drive)

def sample_drive_io(drive_letter):
    sampler = SAMPLERS.get(drive_letter)
    if sampler:
        return sampler.sample()
    
    return {"read": 0, "write": 0}

def get_drive_usage(drive):
    try:
        usage = psutil.disk_usage(drive)
        if not SAMPLERS.get(drive, None):
            SAMPLERS[drive] = DriveIO(drive_letter=drive)
    except FileNotFoundError:
        SAMPLERS.pop(drive, None)
        raise FileNotFoundError(f"Drive {drive} not found.")

    return {
        "total": usage.total,
        "used": usage.used,
        "free": usage.free,
        "perc": usage.percent,

        "original": usage
    }
    
def magnitude_bytes(value):
    value = abs(value)
    if value <= 0:
        return 0
    return int(math.log10(value) / 3)
    
def convert_readable(size_in_bytes, show_diff_sign=True):
    sign_letter = ""
    if show_diff_sign:
        # sign_letter = '→ '
        # if size_in_bytes > 0: sign_letter = "↗ "
        # if size_in_bytes < 0: sign_letter = "↘ "
        # if size_in_bytes > 1024**2: sign_letter = "↑ "
        # if size_in_bytes < -1024**2: sign_letter = "↓ "
        if size_in_bytes > 0: sign_letter = "+"
        if size_in_bytes < 0: sign_letter = "-"
    
    size_in_bytes = abs(size_in_bytes)
    
    binary_size = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    decimal_size = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    size = USE_DECIMAL and 1000 or 1024

    for i, unit in enumerate(USE_DECIMAL and decimal_size or binary_size):
        if size_in_bytes < size ** (i + 1):
            return f"{sign_letter}{size_in_bytes / (size ** i):.2f} {unit}"
        