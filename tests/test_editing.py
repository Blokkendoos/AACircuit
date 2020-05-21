# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from application import REMOVE, INSERT
from application.pos import Pos
from application.controller import Controller


class EditingTest(unittest.TestCase):

    def test_insert_remove(self):

        c = Controller()
        c.on_new()

        # NB test should be run against the default (en_US) component library
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

    def test_cols(self):

        c = Controller()
        c.on_new()

        grid = c.grid

        nr_cols_before = grid.nr_cols

        # private methods do change the grid dimensions
        grid._insert_col(3)
        self.assertEqual(grid.nr_cols, nr_cols_before + 1)

        grid._remove_col(3)
        self.assertEqual(grid.nr_cols, nr_cols_before)

        # the grid dimensions should stay the same
        c.on_grid_col(3, INSERT)
        self.assertEqual(grid.nr_cols, nr_cols_before)

        c.on_grid_col(3, REMOVE)
        self.assertEqual(grid.nr_cols, nr_cols_before)

        c.on_grid_col(3, REMOVE)
        c.on_grid_col(3, INSERT)
        self.assertEqual(grid.nr_cols, nr_cols_before)

        c.on_grid_col(3, REMOVE)
        c.on_undo()
        self.assertEqual(grid.nr_cols, nr_cols_before)

    def test_rows(self):

        c = Controller()
        c.on_new()
        grid = c.grid

        nr_rows_before = c.grid.nr_rows

        # private methods do change the grid dimensions
        grid._insert_row(3)
        self.assertEqual(grid.nr_rows, nr_rows_before + 1)

        grid._remove_row(3)
        self.assertEqual(grid.nr_rows, nr_rows_before)

        # the grid dimensions should stay the same
        c.on_grid_row(3, INSERT)
        self.assertEqual(grid.nr_rows, nr_rows_before)

        c.on_grid_row(3, REMOVE)
        self.assertEqual(grid.nr_rows, nr_rows_before)

        c.on_grid_row(3, REMOVE)
        c.on_grid_row(3, INSERT)
        self.assertEqual(grid.nr_rows, nr_rows_before)

        c.on_grid_row(3, REMOVE)
        c.on_undo()
        self.assertEqual(grid.nr_rows, nr_rows_before)

    def test_erase(self):

        c = Controller()
        c.on_new()

        # NB test should be run against the default (en_US) component library
        c.on_component_changed('AND gate')
        c.on_paste_objects(Pos(4, 2))

        c.on_eraser_selected((5, 5))
        c.on_paste_objects(Pos(5, 2))

        filename = 'tmp/test_edit_erase.aac'
        self.assertTrue(c.on_write_to_file(filename))

    def test_duplicate(self):

        c = Controller()
        c.on_new()

        # NB test should be run against the default (en_US) component library
        c.on_component_changed('AND gate')
        c.on_paste_objects(Pos(4, 2))

        c.on_component_changed('NAND gate')
        c.on_paste_objects(Pos(4, 2))

        rect = (Pos(4, 2), Pos(5, 3))
        c.on_cut(rect)

        filename = 'tmp/test_edit_duplicate.aac'
        self.assertTrue(c.on_write_to_file(filename))
