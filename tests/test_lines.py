# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from application.pos import Pos
from application.controller import Controller


class LinesTest(unittest.TestCase):

    def test_lines(self):

        c = Controller()
        c.on_new()

        start = Pos(10, 10)
        end = Pos(20, 10)

        for type in range(4):
            c.on_paste_line(start, end, type)
            start += Pos(0, 5)
            end += Pos(0, 5)

        filename = 'tmp/test_lines.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_rect(self):

        c = Controller()
        c.on_new()

        start = Pos(10, 10)
        end = Pos(20, 20)

        c.on_paste_rect(start, end)

        filename = 'tmp/test_rect.aac'
        self.assertTrue(c.on_write_to_file(filename))
