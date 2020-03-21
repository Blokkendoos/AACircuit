"""
AACircuit
2020-03-02 JvO
"""

from application.grid import Grid
from application import HORIZONTAL
from application import LINE_HOR, LINE_VERT, TERMINAL1, TERMINAL2, TERMINAL3


class Symbol(Grid):

    def __init__(self, dict=None):

        super(Symbol).__init__()

        if dict is None:
            self._grid = self.default
        else:
            self._grid = dict

    @property
    def default(self):
        # resistor symbol
        grid = [
            [" ", "|", " "],
            [".", "+", "."],
            ["|", " ", "|"],
            ["|", " ", "|"],
            [".", "+", "."],
            [" ", "|", " "]]
        return grid

    def line(self, dir, type, length):

        def terminal():
            print("type:", type)
            if type == '1':
                term = TERMINAL1
            elif type == '2':
                term = TERMINAL2
            elif type == '3':
                term = TERMINAL3
            else:
                term = linechar
            return term

        grid = []

        if dir == HORIZONTAL:
            linechar = LINE_HOR
            row = [terminal()]
            for i in range(length):
                row.append(linechar)
            row.append(terminal())
            grid.append(row)
        else:
            # vertical line
            linechar = LINE_VERT
            grid.append([terminal()])
            for i in range(length):
                grid.append([linechar])
            grid.append([terminal()])

        return grid
