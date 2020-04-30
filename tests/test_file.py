# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from application.pos import Pos
from application.controller import Controller


class FileTest(unittest.TestCase):

    def test_read_write(self):

        c = Controller()

        filename = 'tests/files/test_all.aac'
        self.assertTrue(c.on_read_from_file(filename))

        filename = 'tmp/test_all.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_ascii(self):

        c = Controller()

        c.on_new()

        filename = 'tests/files/test_ascii.txt'
        self.assertTrue(c.on_load_ascii_from_file(filename))

        pos = Pos(0, 0)
        c.on_paste_objects(pos)

        filename = 'tmp/test_ascii.aac'
        self.assertTrue(c.on_write_to_file(filename))
