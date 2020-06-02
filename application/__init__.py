"""
AACircuit
2020-03-02 JvO
"""

import gettext
import locale
import sys
from os import path

# set local language, if supported
try:
    loc = locale.getdefaultlocale()
    lang = loc[0]
    local_lang = gettext.translation('aacircuit', localedir='locale', languages=[lang])
    local_lang.install()
    _ = local_lang.gettext
except Exception as e:  # noqa F841
    _ = gettext.gettext


def get_path_to_data(file_path):
    # when run from within a bundle (created w pyinstaller)
    bundle_dir = getattr(sys, '_MEIPASS', path.abspath(path.dirname(__file__)))
    path_to_dat = path.join(bundle_dir, file_path)
    return path_to_dat


# message levels (css style name too)
INFO = 'info'
WARNING = 'warning'
ERROR = 'error'

# grid cells
CELL_DEFAULT = ' '
CELL_NEW = CELL_DEFAULT
CELL_EMPTY = CELL_DEFAULT
CELL_ERASE = 0x00

# selection action
REMOVE = 'remove'
INSERT = 'insert'

# orientation
HORIZONTAL = 0
VERTICAL = 1
LONGEST_FIRST = 2

# selection state
IDLE = 0
SELECTING = 1
SELECTED = 2
DRAG = 3

# selected item
ERASER = 'eras'
OBJECT = 'obj'
OBJECTS = 'objs'
COMPONENT = 'comp'
CHARACTER = 'char'
TEXT = 'text'
TEXT_BLOCK = 'block'
COL = 'col'
ROW = 'row'
RECT = 'srect'
DRAW_RECT = 'rect'
ARROW = 'arrw'
LINE = 'line'
MAG_LINE = 'magl'
DIR_LINE = 'dirl'

MARK_CHAR = 'X'
