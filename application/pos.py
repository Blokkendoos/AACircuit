"""
AACircuit
2020-03-02 JvO
"""

from application import GRIDSIZE_W, GRIDSIZE_H


class Pos(object):
    """A position on the grid (canvas)."""

    def __init__(self, x, y):
        self._x = int(x)
        self._y = int(y)

    def __add__(self, other):
        x = self._x + other.x
        y = self._y + other.y
        return Pos(x, y)

    def __sub__(self, other):
        x = self._x - other.x
        y = self._y - other.y
        return Pos(x, y)

    def __str__(self):
        return "x:{0} y:{1}".format(self._x, self._y)

    @property
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value

    @property
    def xy(self):
        return (self._x, self._y)

    def snap_to_grid(self):
        """Set position to the nearest (canvas) grid coordinate."""
        (x, y) = (self._x, self._y)
        x -= x % GRIDSIZE_W
        y -= y % GRIDSIZE_H
        self._x = round(x)
        self._y = round(y)

    def grid_rc(self):
        """Map canvas (x,y) position to grid (col,row) coordinates."""
        (x, y) = (self._x, self._y)
        x /= GRIDSIZE_W
        y /= GRIDSIZE_H
        return Pos(x, y)
