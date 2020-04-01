'''
AACircuit
2020-03-02 JvO
'''

import copy

from application import _
from application.grid import Grid
from application import HORIZONTAL, VERTICAL
from application import LINE_HOR, LINE_VERT, TERMINAL1, TERMINAL2, TERMINAL3, TERMINAL4


class Symbol(Grid):

    ORIENTATION = {0: "N", 1: "E", 2: "S", 3: "W"}

    def __init__(self, id=0, dict=None, ori=None):

        super(Symbol, self).__init__()

        self._id = id

        if ori is None:
            self._ori = 0
        else:
            self._ori = ori

        if dict is None:
            self._grid = self.default
        else:
            self._grid = dict

    def __str__(self):
        str = _("symbol id: {0} orientation: {1}").format(self._id, self.ORIENTATION[self._ori])
        return str

    @property
    def id(self):
        return self._id

    @property
    def ori(self):
        return self._ori

    @property
    def default(self):
        # default provides one ("N" orientation) grid only
        grid = {'N': [
            ' ___ ',
            '|__ \\',
            '  / /',
            ' |_| ',
            ' (_) ']}
        return grid

    def copy(self):
        ori = copy.deepcopy(self._ori)
        grid = copy.deepcopy(self._grid)
        return Symbol(self._id, grid, ori)

    def grid(self, ori=None):
        if ori is None:
            ori = self._ori

        if len(self._grid) == 1:
            # TODO separate logic for single char / default symbol?
            # single character or default symbol
            return self._grid[self.ORIENTATION[0]]
        else:
            return self._grid[self.ORIENTATION[ori]]

    def grid_next(self):
        """Return the grid with the next (90° clockwise rotated) orientation for this symbol."""
        self._ori += 1
        self._ori %= 4
        return self._grid[self.ORIENTATION[self._ori]]

    def mirror(self):
        """Return the grid vertically mirrored."""
        if self._grid is None:
            return
            # return [[]]

        # mirror specific characters
        switcher = {'/': '\\',
                    '\\': '/',
                    '<': '>',
                    '>': '<',
                    '(': ')',
                    ')': '('
                    }
        grid = []

        for r, row in enumerate(self._grid[self.ORIENTATION[self._ori]]):
            rev = []
            for c in reversed(row):
                try:
                    rev.append(switcher[c])
                except KeyError:
                    rev.append(c)
            grid.append(rev)

        self._grid[self.ORIENTATION[self._ori]] = grid


class Line(Symbol):

    TERMINAL_TYPE = {'0': None, '1': TERMINAL1, '2': TERMINAL2, '3': TERMINAL3, '4': TERMINAL4}

    def __init__(self, startpos, endpos, type=0):
        super(Line, self).__init__()

        self._id = type
        self._startpos = startpos
        self._endpos = endpos
        self._terminal = self.TERMINAL_TYPE[type]

        self._direction()
        self._line()

    def _direction(self):
        if self._startpos.x == self._endpos.x:
            self._dir = VERTICAL
        elif self._startpos.y == self._endpos.y:
            self._dir = HORIZONTAL
        else:
            self._dir = None

    def _line(self):
        if self._dir == HORIZONTAL:
            grid = self._line_hor()
        elif self._dir == VERTICAL:
            grid = self._line_vert()
        else:
            grid = ['?']

        self._grid = {'N': grid}

    def _line_hor(self):
        grid = []

        if self._terminal is None:
            linechar = LINE_HOR
        else:
            linechar = self._terminal

        row = []
        length = abs(self._endpos.x - self._startpos.x)
        for i in range(length):
            row.append(linechar)
            linechar = LINE_HOR

        if self._terminal is None:
            linechar = LINE_HOR
        else:
            linechar = self._terminal

        row.append(linechar)
        grid.append(row)

        return grid

    def _line_vert(self):
        grid = []

        if self._terminal is None:
            linechar = LINE_VERT
        else:
            linechar = self._terminal

        length = abs(self._endpos.y - self._startpos.y)
        for i in range(length):
            grid.append([linechar])
            linechar = LINE_VERT

        if self._terminal is None:
            linechar = LINE_VERT
        else:
            linechar = self._terminal

        grid.append([linechar])

        return grid
