# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from application.pos import Pos
from application.controller import Controller


class EditingTest(unittest.TestCase):

    def test_insert_remove(self):

        c = Controller()
        c.on_new()

        c.on_component_changed('AND gate')
        c.on_paste_objects(Pos(4, 2))

        c.on_component_changed('NAND gate')
        c.on_paste_objects(Pos(14, 2))

        filename = 'tmp/test_edit_insert.aac'
        self.assertTrue(c.on_write_to_file(filename))

        rect = (Pos(4, 2), Pos(5, 3))
        c.on_cut(rect)

        filename = 'tmp/test_edit_remove.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_erase(self):

        c = Controller()
        c.on_new()

        c.on_component_changed('AND gate')
        c.on_paste_objects(Pos(4, 2))

        c.on_eraser_selected((5, 5))
        c.on_paste_objects(Pos(5, 2))

        filename = 'tmp/test_edit_erase.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_duplicate(self):

        c = Controller()
        c.on_new()

        c.on_component_changed('AND gate')
        c.on_paste_objects(Pos(4, 2))

        c.on_component_changed('NAND gate')
        c.on_paste_objects(Pos(4, 2))

        rect = (Pos(4, 2), Pos(5, 3))
        c.on_cut(rect)

        filename = 'tmp/test_edit_duplicate.aac'
        self.assertTrue(c.on_write_to_file(filename))
