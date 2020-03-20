"""
AACircuit
2020-03-02 JvO
"""

# grid
FONTSIZE = 12
GRIDSIZE_W = 7
GRIDSIZE_H = 16

# selection action
REMOVE = 'remove'
INSERT = 'insert'
HORIZONTAL = 'hor'
VERTICAL = 'vert'

# selection state
IDLE = 0
SELECTING = 1
SELECTED = 2
DRAG = 3

# selected item
COMPONENT = 'comp'
COL = 'col'
ROW = 'row'
RECT = 'rect'
LINE = 'line'
