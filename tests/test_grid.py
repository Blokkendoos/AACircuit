# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from application.grid import Grid
from application.grid_view import Pos


class GridTest(unittest.TestCase):

    def test_default_dimension(self):

        g = Grid()

        self.assertEquals(g.nr_rows, 5)
        self.assertEquals(g.nr_cols, 5)

    def test_content(self):

        g = Grid()

        i = 0
        for r in range(g.nr_rows):
            for c in range(g.nr_cols):
                pos = Pos(c, r)
                g.set_cell(pos, i)
                i += 1

        rect = (Pos(1, 1), Pos(1, 1))
        value = g.rect(rect)[0][0]
        self.assertEquals(value, 6)

        rect = (Pos(4, 4), Pos(4, 4))
        value = g.rect(rect)[0][0]
        self.assertEquals(value, 24)

    def test_fill(self):

        g = Grid()

        i = 0
        for r in range(g.nr_rows):
            for c in range(g.nr_cols):
                pos = Pos(c, r)
                g.set_cell(pos, i)
                i += 1

        c = [["A", "B"], ["C", "D"]]
        g.fill_rect(Pos(0, 0), c)
        print(g)

        g.fill_rect(Pos(3, 3), c)
        print(g)

    def test_erase_rect(self):

        g = Grid()

        i = 0
        for r in range(g.nr_rows):
            for c in range(g.nr_cols):
                pos = Pos(c, r)
                g.set_cell(pos, i)
                i += 1

        rect = (Pos(1, 1), Pos(2, 2))
        g.erase_rect(rect)
        print(g)

    def test_remove(self):

        g = Grid()

        i = 0
        for r in range(g.nr_rows):
            for c in range(g.nr_cols):
                pos = Pos(c, r)
                g.set_cell(pos, i)
                i += 1

        print("removed row 2:")
        g.remove_row(2)
        print(g)

        print("removed column 2:")
        g.remove_col(2)
        print(g)

    def test_insert(self):

        g = Grid()

        i = 0
        for r in range(g.nr_rows):
            for c in range(g.nr_cols):
                pos = Pos(c, r)
                g.set_cell(pos, i)
                i += 1

        print("insert column 2:")
        g.insert_col(2)
        print(g)

        print("insert row 2:")
        g.insert_row(2)
        print(g)
