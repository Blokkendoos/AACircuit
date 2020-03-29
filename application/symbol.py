'''
AACircuit
2020-03-02 JvO
'''

from application.grid import Grid
from application import HORIZONTAL
from application import LINE_HOR, LINE_VERT, TERMINAL1, TERMINAL2, TERMINAL3, TERMINAL4


class Symbol(Grid):

    ORIENTATION = {0: "N", 1: "E", 2: "S", 3: "W"}

    def __init__(self, id=0, dict=None):

        super(Symbol).__init__()

        self._id = id

        if dict is None:
            self._grid = self.default
        else:
            self._grid = dict

        self._ori = 0

    @property
    def id(self):
        return self._id

    @property
    def default(self):
        # resistor symbol
        # FIXME default provides one ("N" orientation) grid only
        grid = {"N": [
            [' ', '|', ' '],
            ['.', '+', '.'],
            ['|', ' ', '|'],
            ['|', ' ', '|'],
            ['.', '+', '.'],
            [' ', '|', ' ']]}
        return grid

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
        """Return the grid with clockwise next orientation for this symbol."""
        self._ori += 1
        self._ori %= 4
        return self.grid(self._ori)

    def line(self, dir, type, length):

        def terminal():
            if type == '1':
                term = TERMINAL1
            elif type == '2':
                term = TERMINAL2
            elif type == '3':
                term = TERMINAL3
            elif type == '4':
                term = TERMINAL4
            else:
                term = None
            return term

        grid = []

        if dir == HORIZONTAL:

            if terminal() is None:
                linechar = LINE_HOR
            else:
                linechar = terminal()

            row = []
            for i in range(length):
                row.append(linechar)
                linechar = LINE_HOR

            if terminal() is None:
                linechar = LINE_HOR
            else:
                linechar = terminal()

            row.append(linechar)
            grid.append(row)
        else:
            # vertical line

            if terminal() is None:
                linechar = LINE_VERT
            else:
                linechar = terminal()

            for i in range(length):
                grid.append([linechar])
                linechar = LINE_VERT

            if terminal() is None:
                linechar = LINE_VERT
            else:
                linechar = terminal()

            grid.append([linechar])

        return grid

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

        # return self
