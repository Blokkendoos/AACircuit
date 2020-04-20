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
JUMP_CHAR = ')'
ML_BEND_CHAR = '+'

# lines
LINE_HOR = '-'
LINE_VERT = '|'
TERMINAL1 = None
TERMINAL2 = 'o'
TERMINAL3 = '+'
TERMINAL4 = "'"
TERMINAL_TYPE = {0: None, 1: TERMINAL1, 2: TERMINAL2, 3: TERMINAL3, 4: TERMINAL4}
