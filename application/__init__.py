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
except Exception as e:
    _ = gettext.gettext

# grid
FONTSIZE = 12
GRIDSIZE_W = 10
GRIDSIZE_H = 16

# default dimensions
DEFAULT_ROWS = 36
DEFAULT_COLS = 72

CELL_DEFAULT = ' '
CELL_NEW = CELL_DEFAULT
CELL_EMPTY = CELL_DEFAULT
CELL_ERASE = 0x00

# draw selection by dragging or click and second-click
SELECTION_DRAG = False

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

# lines
LINE_HOR = '-'
LINE_VERT = '|'
CROSSING = ')'

LOWER_CORNER = "'"
UPPER_CORNER = '.'

TERMINAL1 = None
TERMINAL2 = 'o'
TERMINAL3 = '+'
TERMINAL4 = "'"
TERMINAL_TYPE = {0: None, 1: TERMINAL1, 2: TERMINAL2, 3: TERMINAL3, 4: TERMINAL4}
