# -*- coding: UTF-8 -*-

"""
AACircuit
2020-03-02 JvO
"""

import pickle
import xerox
from pubsub import pub

from application import _


class Grid(object):

    DEFAULT_VALUE = " "  # default cell-value
    NEW_VALUE = " "  # value for inserted cell
    EMPTY = " "  # empty cell-value

    def __init__(self, rows=5, cols=5):
        self._undo_stack = []
        self._grid = [[self.DEFAULT_VALUE] * rows for i in range(cols)]
        # set to True when the grid has been changed
        self._dirty = False

    def __str__(self):
        str = _("number of rows: {0} columns: {1}").format(self.nr_rows, self.nr_cols)
        str += "dirty: {0}\n".format(self.dirty)
        for r in self._grid:
            str += "{0}\n".format(r)
        return str

    # PRIVATE

    def _push_grid(self):
        """Use (Pickle) serialization to implement a simple undo functionality."""
        self._undo_stack.append(pickle.dumps(self._grid))
        pub.sendMessage('UNDO_CHANGED', undo=True)

    def _pop_grid(self, str):
        self._grid = pickle.loads(str)

    # PUBLIC

    @property
    def grid(self):
        return self._grid

    @property
    def dirty(self):
        return self._dirty

    @dirty.setter
    def dirty(self, value):
        self._dirty = value

    @property
    def nr_rows(self):
        return len(self._grid)

    @property
    def nr_cols(self):
        return len(self._grid[0])

    def row(self, row):
        return self._grid[row]

    def col(self, col):
        column = []
        for r in self._grid:
            column.append(r[col])
        return column

    def undo(self):

        print("Grid.undo: Deprecated method")

        # FIXME grid viewport is not resized when the gridsize has been changed (by this undo)
        if len(self._undo_stack) > 0:
            self._pop_grid(self._undo_stack.pop())
        if len(self._undo_stack) == 0:
            pub.sendMessage('UNDO_CHANGED', undo=False)

    def to_str(self):
        return pickle.dumps(self._grid)

    def from_str(self, str):
        self._grid = pickle.loads(str)

    # clipboard

    def copy_to_clipboard(self):
        """
        Copy the content of the grid to the clipboard.
        The rows are copied as ASCII lines, terminated by CR.
        """
        content = ""

        for r in self._grid:
            line = ""
            for c in r:
                line += c
            content += (line + "\n")

        content += _("(created by AACircuit.py © 2020 JvO)")

        xerox.copy(content)

    def paste_from_clipboard(self):
        """
        Copy the content of the clipboard to the grid.
        ASCII lines, terminated by CR, are interpreted as rows.
        """
        print("Deprecated method")

        self._push_grid()

        grid = []
        first_line = True
        content = xerox.paste().splitlines()
        for line in content:
            dict = []
            for char in line:
                dict.append(char)

            # the first line determines the number of columns in the new grid
            if first_line:
                first_line = False
                row_length = len(dict)
            elif len(dict) < row_length:
                for i in range(len(dict), row_length):
                    dict.append(" ")
            elif len(dict) < row_length:
                dict = dict[:row_length]

            grid.append(dict)

        self._grid = grid

        self._dirty = True

    def load_and_paste_from_clipboard(self):
        print("Not yet implemented")

    # grid manipulation

    def cell(self, pos):
        col, row = pos.xy
        # TODO return space or x00?
        if row < self.nr_rows and col < self.nr_cols:
            return self._grid[row][col]
        else:
            return ' '

    def set_cell(self, pos, value):
        row = pos.y
        col = pos.x
        if row < self.nr_rows and col < self.nr_cols:
            self._grid[row][col] = value

    def rect_to_rc(self, rect):
        """Convert the rect view (x,y) coordinates to colum and row start/end values.
        :param rect: (tuple) position (Pos) of the upper left corner (row, column) of the rectangle
        :returns the start and end column and row
        """
        ul = rect[0]
        br = rect[1]
        c_start, r_start = ul.xy
        c_end, r_end = br.xy
        return (c_start, r_start, c_end, r_end)

    def rect(self, rect):
        """
        Return the content of the given rectangle.
        :param rect: the canvas position (Pos) of the upper left corner (row, column) and bottom-rigth corner of the rectangle
        :returns the content of the given rectangle
        """
        content = []

        c_start, r_start, c_end, r_end = self.rect_to_rc(rect)

        # truncate
        if r_end >= self.nr_rows:
            r_end = self.nr_rows
        if c_end >= self.nr_cols:
            r_end = self.nr_cols

        # TODO Padd content?
        for r in range(r_start, r_end):
            content.append(self._grid[r][c_start:c_end])

        return content

    def erase_rect(self, rect):
        """
        Erase a rectangle its content.
        :param rect: rectangle upper-left corner and bottom-right corner (row, column) tuple
        """

        self._push_grid()

        c_start, r_start, c_end, r_end = self.rect_to_rc(rect)

        # truncate
        if r_end >= self.nr_rows:
            r_end = self.nr_rows
        if c_end >= self.nr_cols:
            r_end = self.nr_cols

        for r in range(r_start, r_end):
            for c in range(c_start, c_end):
                self._grid[r][c] = self.EMPTY

        self._dirty = True

    def fill_rect(self, pos, content):
        """
        Fill a rectangle.
        :param pos: rectangle upper left corner (row, column) tuple
        :param content: 2D array
        """
        if len(content) == 0:
            return

        self._push_grid()

        c_start, r_start = pos.xy
        x_max = self.nr_cols
        y_max = self.nr_rows

        y = r_start
        for row in content:
            x = c_start
            for char in row:
                # TODO crude OR (sybol grid OR grid) by ignoring space char
                if char != " ":
                    self._grid[y][x] = char
                x += 1
                if x >= x_max:
                    break
            y += 1
            if y >= y_max:
                break

        self._dirty = True

    def remove_row(self, row):
        # assert row >= 0 and row < self.nr_rows
        if row >= 0 and row < self.nr_rows:
            self._push_grid()
            del self._grid[row]
            self._dirty = True

    def remove_col(self, col):
        # assert col >= 0 and col < self.nr_cols
        if col >= 0 and col < self.nr_cols:
            self._push_grid()
            for r in self._grid:
                del r[col]
            self._dirty = True

    def insert_row(self, row):
        self._push_grid()
        self._grid.insert(row, [self.NEW_VALUE] * self.nr_cols)
        self._dirty = True

    def insert_col(self, col):
        self._push_grid()
        for r in self._grid:
            r.insert(col, self.NEW_VALUE)
        self._dirty = True
