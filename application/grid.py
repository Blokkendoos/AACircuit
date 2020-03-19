# -*- coding: UTF-8 -*-

"""
AACircuit
2020-03-02 JvO
"""

import pickle
import xerox


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
        str = "number of rows: {0} columns: {1} ".format(self.nr_rows, self.nr_cols)
        str += "dirty: {0}\n".format(self.dirty)
        for r in self._grid:
            str += "{0}\n".format(r)
        return str

    # PRIVATE

    def _push_grid(self):
        """Use (Pickle) serialization to implement a simple undo functionality."""
        self._undo_stack.append(pickle.dumps(self._grid))

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
        if len(self._undo_stack) > 0:
            self._pop_grid(self._undo_stack.pop())

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

        content += "(created by AACircuit.py © 2020 JvO)"

        xerox.copy(content)

    def paste_from_clipboard(self):
        """
        Copy the content of the clipboard to the grid.
        ASCII lines, terminated by CR, are interpreted as rows.
        """

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
        None

    # grid manipulation

    def cell(self, row, col):
        return self._grid[row][col]

    def set_cell(self, row, col, value):
        self._grid[row][col] = value

    def pos_to_rc(self, pos, rect):
        """Convert (canvas) position and rect to colum and row start/end values.
        :param pos:  canvas position (Pos) of the upper left corner (row, column) of the rectangle
        :param rect: tuple (width, height)
        :returns the start and end column and row
        """
        c_start, r_start = pos.xy
        c_end, r_end = tuple(map(lambda i, j : i + j, pos.xy, rect))  # noqa: E203
        return (c_start, r_start, c_end, r_end)

    def rect(self, pos, rect):
        """
        Return the content of the given rectangle.
        :param pos:  canvas position (Pos) of the upper left corner (row, column) of the rectangle
        :param rect: tuple (width, height)
        :returns the content of the given rectangle
        """
        content = []

        c_start, r_start, c_end, r_end = self.pos_to_rc(pos, rect)

        # truncate
        if r_end >= self.nr_rows:
            r_end = self.nr_rows
        if c_end >= self.nr_cols:
            r_end = self.nr_cols

        # TODO Padd content?
        for r in range(r_start, r_end):
            content.append(self._grid[r][c_start:c_end])

        return content

    def erase_rect(self, pos, rect):
        """
        Erase a rectangle its content.
        :param pos: rectangle upper left corner (row, column) tuple
        :param rect: tuple (width, height)
        """

        self._push_grid()

        c_start, r_start, c_end, r_end = self.pos_to_rc(pos, rect)

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

        width = len(content[0])
        rect = (width, len(content))

        c_start, r_start, c_end, r_end = self.pos_to_rc(pos, rect)

        # truncate
        if r_end >= self.nr_rows:
            r_end = self.nr_rows
        if c_end >= self.nr_cols:
            width = width + self.nr_cols - c_end
            c_end = self.nr_cols

        i = 0
        for r in range(r_start, r_end):
            # crude OR (sybol grid OR grid) by ignoring space char
            # self._grid[r][c_start:c_end] = content[i][:width]
            j = 0
            for c in range(c_start, c_end):
                if content[i][j] != " ":
                    self._grid[r][c] = content[i][j]
                j += 1
            i += 1

        self._dirty = True

    def remove_row(self, row):
        # assert row >= 0 and row < len(self._grid)
        self._push_grid()
        del self._grid[row]
        self._dirty = True

    def remove_col(self, col):
        # assert col >= 0 and col < len(self._grid[0])
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
