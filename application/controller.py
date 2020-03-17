"""
AACircuit.py
2020-03-02 JvO
"""

from pubsub import pub

from application.grid import Grid
from application.main_window import MainWindow
from application.component_library import ComponentLibrary


class Controller(object):

    def __init__(self):

        # setup MVC

        self.grid = Grid(72, 36)  # the ASCII grid

        self.gui = MainWindow()

        self.components = ComponentLibrary()
        all_components = [key for key in self.components.get_dict()]
        print("{0} libraries loaded, total number of components: {1}".format(self.components.nr_libraries(),
                                                                             self.components.nr_components()))
        # messages

        pub.sendMessage('ALL_COMPONENTS', list=all_components)
        pub.sendMessage('GRID', grid=self.grid)

        # subscriptions

        pub.subscribe(self.on_component_changed, 'COMPONENT_CHANGED')
        pub.subscribe(self.on_rotate_symbol, 'ROTATE_SYMBOL')
        pub.subscribe(self.on_paste_symbol, 'PASTE_SYMBOL')
        pub.subscribe(self.on_undo, 'UNDO')

        # insert/remove rows or columns
        pub.subscribe(self.on_insert_col, 'INSERT_COL')
        pub.subscribe(self.on_insert_row, 'INSERT_ROW')
        pub.subscribe(self.on_remove_col, 'REMOVE_COL')
        pub.subscribe(self.on_remove_row, 'REMOVE_ROW')

        # clipboard
        pub.subscribe(self.on_copy, 'COPY_TO_CLIPBOARD')
        pub.subscribe(self.on_paste, 'PASTE_FROM_CLIPBOARD')
        pub.subscribe(self.on_load, 'LOAD_AND_PASTE_FROM_CLIPBOARD')

    def show_all(self):
        self.gui.show_all()

    def on_undo(self):
        self.grid.undo()
        pub.sendMessage('GRID', grid=self.grid)

    # grid manipulation

    def on_insert_col(self, col):
        self.grid.insert_col(col)

    def on_insert_row(self, row):
        self.grid.insert_row(row)

    def on_remove_col(self, col):
        self.grid.remove_col(col)

    def on_remove_row(self, row):
        self.grid.remove_row(row)

    def on_component_changed(self, label):
        grid = self.components.get_grid(label)
        pub.sendMessage('SYMBOL_SELECTED', grid=grid)

    def on_rotate_symbol(self):
        grid = self.components.get_grid_next()
        pub.sendMessage('SYMBOL_SELECTED', grid=grid)

    def on_paste_symbol(self, pos):
        symbol_grid = self.components.get_grid_current()
        self.grid.fill_rect(pos, symbol_grid)

    # clipboard

    def on_copy(self):
        self.grid.copy_to_clipboard()

    def on_paste(self):
        self.grid.paste_from_clipboard()
        pub.sendMessage('GRID', grid=self.grid)

    def on_load(self):
        self.grid.load_and_paste_from_clipboard()
        pub.sendMessage('GRID', grid=self.grid)
