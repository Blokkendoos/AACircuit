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

    def test_read_aac(self):

        c = Controller()

        filename = 'tests/files/test_tr_circuit.aac'
        self.assertTrue(c.on_read_from_file(filename))

    def test_read_ascii(self):

        c = Controller()
        c.on_new()

        filename = 'tests/files/test_ascii.txt'
        self.assertTrue(c.on_load_ascii_from_file(filename))

        pos = Pos(0, 0)
        c.on_paste_objects(pos)

        filename = 'tmp/test_ascii.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_import_aacircuit(self):

        c = Controller()
        c.legacy = True

        filename = 'tests/files/original_741.aac'
        self.assertTrue(c.on_read_from_file(filename))

        filename = 'tmp/741.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_export_ascii(self):

        c = Controller()

        filename = 'tests/files/test_all.aac'
        self.assertTrue(c.on_read_from_file(filename))

        filename = 'tmp/test_all.txt'
        self.assertTrue(c.on_write_to_ascii_file(filename))

    def test_export_pdf(self):

        c = Controller()

        filename = 'tests/files/test_all.aac'
        self.assertTrue(c.on_read_from_file(filename))

        # FIXME
        # To avoid using grid_view methods, use the controller to pass to grid_view.
        # With the disadvantage of not being able to check the outcome here.
        # Instead, visually check the existence and content of the PDF file.
        filename = 'tmp/test_all.pdf'
        c.on_export_as_pdf(filename)
