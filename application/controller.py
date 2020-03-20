"""
AACircuit.py
2020-03-02 JvO
"""

from pubsub import pub

from application.grid import Grid
from application.symbol import Symbol
from application.main_window import MainWindow
from application.component_library import ComponentLibrary


class Controller(object):

    def __init__(self):

        # setup MVC

        self.grid = Grid(72, 36)  # the ASCII grid

        self.gui = MainWindow()

        self.components = ComponentLibrary()
        self.symbol = Symbol()

        all_components = [key for key in self.components.get_dict()]
        print("{0} libraries loaded, total number of components: {1}".format(self.components.nr_libraries(),
                                                                             self.components.nr_components()))
        # messages

        pub.sendMessage('ALL_COMPONENTS', list=all_components)
        pub.sendMessage('GRID', grid=self.grid)

        # subscriptions

        pub.subscribe(self.on_component_changed, 'COMPONENT_CHANGED')
        pub.subscribe(self.on_rotate_symbol, 'ROTATE_SYMBOL')
        pub.subscribe(self.on_mirror_symbol, 'MIRROR_SYMBOL')
        pub.subscribe(self.on_paste_symbol, 'PASTE_SYMBOL')
        pub.subscribe(self.on_undo, 'UNDO')

        # insert/remove rows or columns
        pub.subscribe(self.on_insert_col, 'INSERT_COL')
        pub.subscribe(self.on_insert_row, 'INSERT_ROW')
        pub.subscribe(self.on_remove_col, 'REMOVE_COL')
        pub.subscribe(self.on_remove_row, 'REMOVE_ROW')

        # clipboard
        pub.subscribe(self.on_copy_to_clipboard, 'COPY_TO_CLIPBOARD')
        pub.subscribe(self.on_paste_from_clipboard, 'PASTE_FROM_CLIPBOARD')
        pub.subscribe(self.on_load_and_paste_from_clipboard, 'LOAD_AND_PASTE_FROM_CLIPBOARD')

        pub.subscribe(self.on_cut, 'CUT')
        pub.subscribe(self.on_copy, 'COPY')
        pub.subscribe(self.on_paste, 'PASTE')
        pub.subscribe(self.on_delete, 'DELETE')

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
        self.symbol = Symbol(grid)
        pub.sendMessage('SYMBOL_SELECTED', symbol=self.symbol)

    def on_rotate_symbol(self):
        grid = self.components.get_grid_next()
        self.symbol = Symbol(grid)
        pub.sendMessage('SYMBOL_SELECTED', symbol=self.symbol)

    def on_mirror_symbol(self):
        grid = self.symbol.mirror()
        self.symbol = Symbol(grid)
        pub.sendMessage('SYMBOL_SELECTED', symbol=self.symbol)

    def on_paste_symbol(self, pos):
        self.grid.fill_rect(pos, self.symbol.grid)

    # cut and paste

    def on_cut(self, pos, rect):
        # print("CUT pos:", pos, " w:", w, "h:", h)
        self.grid.erase_rect(pos, rect)

    def on_copy(self):
        self.grid.copy_to_clipboard()

    def on_paste(self):
        self.grid.copy_to_clipboard()

    def on_delete(self):
        self.grid.copy_to_clipboard()

    # clipboard

    def on_copy_to_clipboard(self):
        self.grid.copy_to_clipboard()

    def on_paste_from_clipboard(self):
        self.grid.paste_from_clipboard()
        pub.sendMessage('GRID', grid=self.grid)

    def on_load_and_paste_from_clipboard(self):
        self.grid.load_and_paste_from_clipboard()
        pub.sendMessage('GRID', grid=self.grid)
