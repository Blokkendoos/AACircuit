'''
AACircuit
2020-03-02 JvO
'''

import copy

from application import _
from application.pos import Pos
from application import HORIZONTAL, VERTICAL
from application import LINE_HOR, LINE_VERT, TERMINAL_TYPE


class Symbol(object):

    ORIENTATION = {0: "N", 1: "E", 2: "S", 3: "W"}

    def __init__(self, id=0, dict=None, ori=None):

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

    @property
    def grid(self):
        if len(self._grid) == 1:
            # TODO separate logic for single char / default symbol?
            # single character or default symbol
            return self._grid[self.ORIENTATION[0]]
        else:
            return self._grid[self.ORIENTATION[self._ori]]

    def grid_next(self):
        """Return the grid with the next (90° clockwise rotated) orientation for this symbol."""
        self._ori += 1
        self._ori %= 4
        return self._grid[self.ORIENTATION[self._ori]]

    def paste(self, pos, grid):
        """Paste symbol into the target grid.

        :param pos: the (col,row) coordinate of the upper left position of the symbol grid in the target grid
        :param grid: the target grid
        """
        grid.fill_rect(pos, self.grid)

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

    def __init__(self, startpos, endpos, type=0):
        super(Line, self).__init__()

        self._id = type
        self._startpos = startpos
        self._endpos = endpos
        self._terminal = TERMINAL_TYPE[type]

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

    def paste(self, pos, grid):

        start = self._startpos
        end = self._endpos

        offset = pos - start
        start = pos
        end += offset

        # print("start:", start, " end:", end)

        if self._dir == HORIZONTAL:
            grid = self._paste_hor(start, end, grid)
        elif self._dir == VERTICAL:
            grid = self._paste_vert(start, end, grid)

    def _paste_hor(self, pos, end, grid):

        if self._terminal is None:
            linechar = LINE_HOR
        else:
            linechar = self._terminal

        incr = Pos(1, 0)
        while pos < end:
            grid.set_cell(pos, linechar)
            linechar = LINE_HOR
            pos += incr

        if self._terminal is None:
            grid.set_cell(pos, LINE_HOR)
        else:
            grid.set_cell(pos, self._terminal)

    def _paste_vert(self, pos, end, grid):

        if self._terminal is None:
            linechar = LINE_VERT
        else:
            linechar = self._terminal

        incr = Pos(0, 1)
        while pos < end:
            grid.set_cell(pos, linechar)
            linechar = LINE_VERT
            pos += incr

        if self._terminal is None:
            grid.set_cell(pos, LINE_VERT)
        else:
            grid.set_cell(pos, self._terminal)


class Rect(Symbol):

    def __init__(self, startpos, endpos):
        super(Rect, self).__init__()

        self._startpos = startpos
        self._endpos = endpos

        self._rect()

    def _rect(self):

        ul = self._startpos
        ur = Pos(self._endpos.x, self._startpos.y)
        bl = Pos(self._startpos.x, self._endpos.y)
        br = self._endpos

        # print("ul:", ul, " ur:", ur, "\nbl:", bl, "br:", br)

        type = '3'

        line1 = Line(ul, ur, type)
        line2 = Line(ur, br, type)
        line3 = Line(br, bl, type)
        line4 = Line(bl, ul, type)

        grid = []
        grid.extend(line1.grid)
        grid.extend(line2.grid)
        grid.extend(line3.grid)

        self._grid = {'N': grid}

    def paste(self, pos, grid):

        start = self._startpos
        end = self._endpos

        offset = pos - start
        start = pos
        end += offset

        ul = start
        ur = Pos(end.x, start.y)
        bl = Pos(start.x, end.y)
        br = end

        # print("ul:", ul, " ur:", ur, "\nbl:", bl, "br:", br)

        type = '3'

        line1 = Line(ul, ur, type)
        line2 = Line(ur, br, type)
        line3 = Line(bl, br, type)
        line4 = Line(ul, bl, type)

        line1.paste(ul, grid)
        line2.paste(ur, grid)
        line3.paste(bl, grid)
        line4.paste(ul, grid)
