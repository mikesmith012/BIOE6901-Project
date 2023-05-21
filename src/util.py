"""
util.py

Contains static definitions specifically used for this project.

see "doc/util.md" for more details

"""

__author__ = "Mike Smith"
__email__ = "dongming.shi@uqconnect.edu.au"
__date__ = "22/04/2023"
__status__ = "Prototype"
__credits__ = ["Agnethe Kaasen", "Live Myklebust", "Amber Spurway"]


""" default path for csv files to be saved """
DEFAULT_FILE_PATH = "./files"

""" pre-defined colours (b, g, r) """
RED = (0, 0, 255)
GREEN = (0, 255, 0)
BLUE = (255, 0, 0)
YELLOW = (0, 255, 255)
CYAN = (255, 255, 0)
MAGENTA = (255, 0, 255)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

""" max frame dimensions (full-hd): 1920 x 1080 """
FRAME_WIDTH = 1920
FRAME_HEIGHT = 1080
FRAME_ORIGIN = 0

""" init tuple (used for bounding box) """
INIT = (0, 0)

""" co-ordinate definitions """
X = 0
Y = 1

""" positional min and max thresholds """
MIN = 0.02
MAX = 0.98

""" visibility threshold """
VIS = 0.5

""" input source definitions """
VIDEO = 0
WEBCAM = 1

""" supported files """
FILE_NOT_SUPPORTED = -1
CSV = 0
MP4 = 1
