"""
AACircuit
2020-03-02 JvO
"""

import gettext
import locale

# set local language, if supported
try:
    loc = locale.getdefaultlocale()
    lang = loc[0]
    local_lang = gettext.translation('aacircuit', localedir='locale', languages=[lang])
    local_lang.install()
    _ = local_lang.gettext
except Exception as e:  # noqa F841
    _ = gettext.gettext

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
OBJECTS = 'objs'
COMPONENT = 'comp'
CHARACTER = 'char'
TEXT = 'text'
TEXT_BLOCK = 'block'
COL = 'col'
ROW = 'row'
RECT = 'srect'
DRAW_RECT = 'rect'
LINE = 'line'
MAG_LINE = 'magl'
DIR_LINE = 'dirl'

DEFAULT_COMPONENT_KEY = 'Resistor'
MARK_CHAR = 'X'
