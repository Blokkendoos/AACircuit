# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from application.pos import Pos
from application.symbol import Line
from application.controller import Controller


class LinesTest(unittest.TestCase):

    def test_lines(self):

        c = Controller()
        c.on_new()

        start = Pos(5, 5)
        end = Pos(15, 5)

        line_types = (Line.MLINE, Line.LINE1, Line.LINE2, Line.LINE3, Line.LINE4)

        for type in line_types:
            c.on_paste_line(start, end, type)
            start += Pos(0, 5)
            end += Pos(0, 5)

        filename = 'tmp/test_lines.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_rect(self):

        c = Controller()
        c.on_new()

        start = Pos(5, 5)
        end = Pos(15, 15)

        c.on_paste_rect(start, end)

        filename = 'tmp/test_rect.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_magic_line(self):

        c = Controller()
        c.on_new()

        # connect rectangle sides
        start = Pos(5, 5)
        end = Pos(15, 15)
        c.on_paste_rect(start, end)
        c.on_paste_mag_line(Pos(8, 5), Pos(15, 10))

        # connect component to line
        c.on_paste_line(Pos(5, 2), Pos(31, 2), 1)
        c.on_component_changed('AND gate')
        c.on_paste_objects(Pos(25, 5))

        c.on_paste_mag_line(Pos(24, 6), Pos(15, 6))
        c.on_paste_mag_line(Pos(24, 8), Pos(20, 2))

        filename = 'tmp/test_magic_line.aac'
        self.assertTrue(c.on_write_to_file(filename))
