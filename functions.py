import math, psutil, sys

# Optional: use decimal vs binary
USE_DECIMAL = True

# Global sampler dict (like your SAMPLERS)
SAMPLERS = {}

# -------------------
# Cross-platform drive I/O sampler
class DriveIO:
    def __init__(self, drive_letter=None):
        self.drive = drive_letter
        # For Linux, we just store previous read/write values
        self.prev_read = 0
        self.prev_write = 0
        self.prev_time = psutil.time.time()
        # Get initial counters
        counters = self._get_counters()
        self.prev_read = counters["read"]
        self.prev_write = counters["write"]

    def _get_counters(self):
        if sys.platform.startswith("win"):
            # Windows: you could implement win32pdh code here if needed
            return {"read": 0, "write": 0}
        else:
            # Linux: match disk by mountpoint
            partitions = psutil.disk_partitions()
            part = next((p for p in partitions if p.mountpoint == self.drive), None)
            if not part:
                return {"read": 0, "write": 0}
            # e.g., '/dev/sda1' -> 'sda'
            disk_name = part.device.split("/")[-1]
            io_counters = psutil.disk_io_counters(perdisk=True)
            if disk_name in io_counters:
                io = io_counters[disk_name]
                return {"read": io.read_bytes, "write": io.write_bytes}
            else:
                return {"read": 0, "write": 0}

    def sample(self):
        counters = self._get_counters()
        return counters

# -------------------
# Convenience functions
def sample_drive_io(drive_letter):
    if drive_letter not in SAMPLERS:
        SAMPLERS[drive_letter] = DriveIO(drive_letter)
    return SAMPLERS[drive_letter].sample()

def get_drive_usage(drive):
    """Return total/used/free/percent for a mountpoint"""
    try:
        usage = psutil.disk_usage(drive)
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
    if value <= 0: return 0
    return int(math.log10(value) / 3)

def convert_readable(size_in_bytes, show_diff_sign=False):
    sign_letter = ""
    if show_diff_sign:
        if size_in_bytes > 0: sign_letter = "+"
        if size_in_bytes < 0: sign_letter = "-"
    size_in_bytes = abs(size_in_bytes)

    binary_size = ["B", "KiB", "MiB", "GiB", "TiB", "PiB", "EiB", "ZiB", "YiB"]
    decimal_size = ["B", "KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]
    size = 1000 if USE_DECIMAL else 1024

    for i, unit in enumerate(decimal_size if USE_DECIMAL else binary_size):
        if size_in_bytes < size ** (i + 1):
            return f"{sign_letter}{size_in_bytes / (size ** i):.2f} {unit}"