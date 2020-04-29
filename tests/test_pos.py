# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from application.pos import Pos


class PosTest(unittest.TestCase):

    def test_in_rect(self):

        a = Pos(10, 15)
        b = Pos(12, 21)

        ul = Pos(9, 14)
        br = Pos(12, 20)
        r = (ul, br)

        self.assertTrue(a.in_rect(r))
        self.assertFalse(b.in_rect(r))

    def test_comparison(self):

        a = Pos(10, 15)
        b = Pos(12, 21)

        self.assertTrue(a < b)
        self.assertFalse(a > b)
        self.assertTrue(a <= b)
        self.assertFalse(a >= b)

    def test_conversion(self):

        a = Pos(10, 15)
        b = Pos(12, 21)

        print("a.grid_rc: {}".format(a.grid_rc()))
        print("a.view_xy: {}".format(a.view_xy()))

        a.snap_to_grid()
        print("a.snap_to_grid: {}".format(a))

        b = Pos(10, 16)
        print("b.grid_rc: {}".format(b.grid_rc()))
        print("b.view_xy: {}".format(b.view_xy()))
        b.snap_to_grid()
        print("b.snap_to_grid: {}".format(b))

        x = Pos(9, 15)
        print("x:", x)
        x.snap_to_grid()
        print("x.snap_to_grid: {}".format(x))
        print("x.grid_rc: {}".format(x.grid_rc()))

        x = Pos(11, 17)
        print("x:", x)
        x.snap_to_grid()
        print("x.snap_to_grid: {}".format(x))
        print("x.grid_rc: {}".format(x.grid_rc()))

        x = Pos(21, 33)
        print("x:", x)
        x.snap_to_grid()
        print("x.snap_to_grid: {}".format(x))
        print("x.grid_rc: {}".format(x.grid_rc()))

        c = b.grid_rc()
        d = c.view_xy()
        self.assertTrue(b == d)
