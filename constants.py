import string, os
import global_functions

# Program constants
DRIVES = ['%s:' % d for d in string.ascii_uppercase if os.path.exists('%s:' % d)]
PROGRAM_NAME = "Encythe's Disk Analyzer"

# Configuration
UNIT = 1 # How long to wait for between samples, in seconds
HISTORY = 60  # Number of units to keep history for
USE_DECIMAL = False # Whether to use decimal (1000) or binary (1024) prefixes

# Fonts
HEADER_FONT = "Barlow"
FONT = "Barlow"

# Color constants, again, not used all that much
RED = "color: rgb(255, 85, 85);"
GREEN = "color: rgb(85, 255, 85);"
BLUE = "color: rgb(85, 85, 255);"
WHITE = "color: rgb(255, 255, 255);"
YELLOW = "color: rgb(255, 255, 85);"
SATURATION = "50%"

# Thresholds, but not really used except for "WARNING"
NOMINAL = 25
CAUTION = 75
WARNING = 90
TERMINAL = 95

# I/O Counter IDs
PDH_OBJECT_LOGICALDISK = global_functions.get_counter_from_id(236)
PDH_COUNTER_DISK_READ_BYTES_PER_SEC = global_functions.get_counter_from_id(220)
PDH_COUNTER_DISK_WRITE_BYTES_PER_SEC = global_functions.get_counter_from_id(222)