#!/usr/bin/env python

from application.grid_view import Pos
from application.grid import Grid


if __name__ == "__main__":

    g = Grid()
    i = 0
    for r in range(g.nr_rows):
        for c in range(g.nr_cols):
            pos = Pos(c, r)
            g.set_cell(pos, i)
            i += 1

    print(g)

    rect = (Pos(1, 1), Pos(1, 1))
    print("RECT (1,1): {0}".format(g.rect(rect)))

    rect = (Pos(4, 4), Pos(4, 4))
    print("RECT (4,4): {0}".format(g.rect(rect)))

    c = [["A", "B"], ["C", "D"]]
    g.fill_rect(Pos(0, 0), c)
    print(g)

    g.fill_rect(Pos(3, 3), c)
    print(g)

    rect = (Pos(1, 1), Pos(2, 2))
    g.erase_rect(rect)
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
