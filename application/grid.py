# -*- coding: UTF-8 -*-

"""
AACircuit
2020-03-02 JvO
"""

import xerox

from application import _
from application import CELL_DEFAULT, CELL_EMPTY, CELL_NEW, CELL_ERASE


class Grid(object):

    def __init__(self, cols=5, rows=5):
        self._grid = [[CELL_DEFAULT] * cols for i in range(rows)]

    def __str__(self):
        str = _("number of rows: {0} columns: {1}\n").format(self.nr_rows, self.nr_cols)
        for r in self._grid:
            str += "{0}\n".format(r)
        return str

    @property
    def grid(self):
        return self._grid

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
            # hex zero 'erases' content
            if value == CELL_ERASE:
                self._grid[row][col] = CELL_EMPTY
            # space character is 'transparent'
            elif value != ' ':
                self._grid[row][col] = value

    def rect_to_rc(self, rect):
        """Convert the rect to colum and row start/end values.
        :param rect: (tuple) position (Pos) of the upper left corner (row, column) of the rectangle
        :returns the start and end column and row
        """
        ul = rect[0]
        br = rect[1]
        c_start, r_start = ul.xy
        c_end = br.x + 1
        r_end = br.y + 1
        return (c_start, r_start, c_end, r_end)

    def erase(self):
        """Erase all grid content."""
        rows = self.nr_rows
        cols = self.nr_cols
        self._grid = [[CELL_DEFAULT] * cols for i in range(rows)]

    def rect(self, rect):
        """
        Return the content of the given rectangle.
        :param rect: the canvas position (Pos) of the upper left corner (row, column) and bottom-right corner of the rectangle
        :returns the content of the given rectangle
        """

        print("Obsolete method: ", self.rect.__name__)

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

        print("Obsolete method: ", self.erase_rect.__name__)

        c_start, r_start, c_end, r_end = self.rect_to_rc(rect)

        # truncate
        if r_end >= self.nr_rows:
            r_end = self.nr_rows
        if c_end >= self.nr_cols:
            r_end = self.nr_cols

        for r in range(r_start, r_end):
            for c in range(c_start, c_end):
                self._grid[r][c] = CELL_EMPTY

    def fill_rect(self, pos, content):
        """
        Fill a rectangle.
        :param pos: rectangle upper left corner (row, column) tuple
        :param content: 2D array
        """

        print("Obsolete method: ", self.fill_rect.__name__)

        if len(content) == 0:
            return

        c_start, r_start = pos.xy
        x_max = self.nr_cols
        y_max = self.nr_rows

        y = r_start
        for row in content:
            x = c_start
            for char in row:
                # hex zero 'erases' content
                if char == CELL_ERASE:
                    self._grid[y][x] = CELL_EMPTY
                # space character is 'transparent'
                elif char != ' ':
                    self._grid[y][x] = char
                x += 1
                if x >= x_max:
                    break
            y += 1
            if y >= y_max:
                break

    def remove_row(self, row):
        # assert row >= 0 and row < self.nr_rows
        if row >= 0 and row < self.nr_rows:
            del self._grid[row]

    def remove_col(self, col):
        # assert col >= 0 and col < self.nr_cols
        if col >= 0 and col < self.nr_cols:
            for r in self._grid:
                del r[col]

    def insert_row(self, row):
        self._grid.insert(row, [CELL_NEW] * self.nr_cols)

    def insert_col(self, col):
        for r in self._grid:
            r.insert(col, CELL_NEW)

    def resize(self, cols, rows):

        if self.nr_cols < cols:
            for cnt in range(cols - self.nr_cols):
                self.insert_col(self.nr_cols)

        elif self.nr_cols > cols:
            for cnt in range(self.nr_cols - cols):
                self.remove_col(self.nr_cols - 1)

        if self.nr_rows < rows:
            for cnt in range(rows - self.nr_rows):
                self.insert_row(self.nr_rows)

        elif self.nr_rows > rows:
            for cnt in range(self.nr_rows - rows):
                self.remove_row(self.nr_rows - 1)
