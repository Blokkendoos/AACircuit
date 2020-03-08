"""
AACircuit
2020-03-02 JvO
"""


class Grid(object):

    def __init__(self, rows=5, cols=5):
        # https://snakify.org/en/lessons/two_dimensional_lists_arrays/
        self._grid = [[0] * rows for i in range(cols)]
        # https://www.geeksforgeeks.org/python-using-2d-arrays-lists-the-right-way/
        # self._grid = [[0 for i in range(cols)] for j in range(rows)]
        self._dirty = False

    def __str__(self):
        str = "number of rows: {0} columns: {1} ".format(self.nr_rows, self.nr_cols)
        str += "dirty: {0}\n".format(self.dirty)
        for r in self._grid:
            str += "{0}\n".format(r)
        return str

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

    def cell(self, row, col):
        return self._grid[row][col]

    def set_cell(self, row, col, value):
        self._grid[row][col] = value

    def remove_row(self, row):
        # assert row >= 0 and row < len(self._grid)

        del self._grid[row]
        self._dirty = True

    def remove_col(self, col):
        # assert col >= 0 and col < len(self._grid[0])

        for r in self._grid:
            del r[col]

        self._dirty = True

    def insert_row(self, row):
        self._grid.insert(row, ["x"] * self.nr_cols)
        self._dirty = True

    def insert_col(self, col):
        for r in self._grid:
            r.insert(col, "x")
        self._dirty = True


if __name__ == "__main__":

    g = Grid()
    i = 0
    for r in range(g.nr_rows):
        for c in range(g.nr_cols):
            g.set_cell(r, c, i)
            i += 1

    print(g)

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
