"""
AACircuit
2020-03-02 JvO
"""

from application.grid import Grid


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
