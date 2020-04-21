"""
AACircuit
2020-03-02 JvO
"""

from application import GRIDSIZE_W, GRIDSIZE_H
from math import sqrt


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

    def __eq__(self, other):
        return (self._x == other.x and self._y == other.y)

    def __gt__(self, other):
        return (sqrt(self._x**2 + self._y**2) > sqrt(other._x**2 + other._y**2))

    def __lt__(self, other):
        return (sqrt(self._x**2 + self._y**2) < sqrt(other._x**2 + other._y**2))

    def __ge__(self, other):
        return not (self < other)

    def __le__(self, other):
        return not (self > other)

    def __str__(self):
        """Return coordinates as string: e.g.: "10,12"."""
        return "{0},{1}".format(self._x, self._y)

    def __hash__(self):
        return hash((self._x, self._y))

    def __ne__(self, other):
        return not(self == other)

    @property
    def x(self):
        return self._x

    @ x.setter
    def x(self, value):
        self._x = value

    @property
    def y(self):
        return self._y

    @ y.setter
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
        self._x = x
        self._y = y

    def grid_rc(self):
        """Map canvas (x,y) position to grid (col,row) coordinates."""
        (x, y) = (self._x, self._y)
        x /= GRIDSIZE_W
        y /= GRIDSIZE_H
        return Pos(x, y)

    def view_xy(self):
        """Map grid (col,row) coordinates to canvas (x,y) position."""
        (x, y) = (self._x, self._y)
        x *= GRIDSIZE_W
        y *= GRIDSIZE_H
        return Pos(x, y)

    def in_rect(self, rect):
        """
        Check if this point lies within the given rect.

        :param rect: list with the upper left (Pos) and bottom right (Pos) coordinates of the rectangle
        :return True if the point lies within the rect, otherwise False
        """
        (ul, br) = rect
        if (self._x >= ul.x and self._x <= br.x and  # noqa W503
                self._y >= ul.y and self._y <= br.y):
            return True
        else:
            return False
