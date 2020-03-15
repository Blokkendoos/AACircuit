"""
AACircuit
2020-03-02 JvO
"""

import pickle


class Grid(object):

    DEFAULT_VALUE = "/"  # default cell-value
    NEW_VALUE = "x"  # value for inserted cell
    EMPTY = " "  # empty cell-value

    def __init__(self, rows=5, cols=5):

        # https://snakify.org/en/lessons/two_dimensional_lists_arrays/
        self._grid = [[self.DEFAULT_VALUE] * rows for i in range(cols)]

        self._undo_stack = []

        # https://www.geeksforgeeks.org/python-using-2d-arrays-lists-the-right-way/
        # self._grid = [[0 for i in range(cols)] for j in range(rows)]
        self._dirty = False

    def __str__(self):

        str = "number of rows: {0} columns: {1} ".format(self.nr_rows, self.nr_cols)
        str += "dirty: {0}\n".format(self.dirty)
        for r in self._grid:
            str += "{0}\n".format(r)

        return str

    # PRIVATE

    def _save_grid(self):
        """Use (Pickle) serialization to implement a simple, and rude, undo functionality."""
        self._undo_stack.append(pickle.dumps(self._grid))

    def _restore_grid(self, str):
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
            self._restore_grid(self._undo_stack.pop())

    def cell(self, row, col):
        return self._grid[row][col]

    def set_cell(self, row, col, value):
        self._grid[row][col] = value

    def pos_to_rc(self, pos, rect):
        """Convert position and rect to colum and row start/end values."""
        c_start, r_start = pos
        c_end, r_end = tuple(map(lambda i, j : i + j, pos, rect))  # noqa: E203
        # print("col_start:{0} _end:{1}  row_start:{2} _end:{3}".format(c_start, r_start, c_end, r_end))
        return (c_start, r_start, c_end, r_end)

    def rect(self, pos, rect):
        """
        Return the content of the given rectangle.
        :param pos: rectangle upper left corner (row, column) tuple
        :param rect: tuple (width, height)
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

        self._save_grid()

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

        self._save_grid()

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
            self._grid[r][c_start:c_end] = content[i][:width]
            i += 1

        self._dirty = True

    def remove_row(self, row):
        # assert row >= 0 and row < len(self._grid)

        self._save_grid()

        del self._grid[row]
        self._dirty = True

    def remove_col(self, col):
        # assert col >= 0 and col < len(self._grid[0])

        self._save_grid()

        for r in self._grid:
            del r[col]

        self._dirty = True

    def insert_row(self, row):
        self._save_grid()

        self._grid.insert(row, [self.NEW_VALUE] * self.nr_cols)

        self._dirty = True

    def insert_col(self, col):
        self._save_grid()

        for r in self._grid:
            r.insert(col, self.NEW_VALUE)

        self._dirty = True


if __name__ == "__main__":

    g = Grid()
    i = 0
    for r in range(g.nr_rows):
        for c in range(g.nr_cols):
            g.set_cell(r, c, i)
            i += 1

    print(g)

    print("RECT (1,1): {0}".format(g.rect((1, 1), (2, 2))))
    print("RECT (4,4): {0}".format(g.rect((4, 4), (4, 4))))

    c = [["A", "B"], ["C", "D"]]
    g.fill_rect((0, 0), c)
    print(g)

    g.fill_rect((3, 3), c)
    print(g)

    g.erase_rect((1, 1), (2, 2))
    print(g)

    # exit(0)

    g.dirty = False
    print("removed row 2:")
    g.remove_row(2)
    print(g)

    g.dirty = False
    print("insert row 2:")
    g.insert_row(2)
    print(g)

    g.dirty = False
    print("removed column 2:")
    g.remove_col(2)
    print(g)

    g.dirty = False
    print("insert column 2:")
    g.insert_col(2)
    print(g)

    g.dirty = False
    print("removed column 0:")
    g.remove_col(0)
    print(g)

    g.dirty = False
    print("removed column 2:")
    g.remove_col(2)
    print(g)

    g.dirty = False
    print("unchanged:")
    print(g)

    print("row 2: {0}".format(g.row(2)))
    print("col 2: {0}".format(g.col(2)))
