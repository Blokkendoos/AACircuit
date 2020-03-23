"""
AACircuit.py
2020-03-02 JvO
"""

from pubsub import pub

from application.grid import Grid
from application.symbol import Symbol
from application.main_window import MainWindow
from application.component_library import ComponentLibrary
from application.file import FileChooserWindow


class Controller(object):

    def __init__(self):

        # setup MVC

        self.grid = Grid(72, 36)  # the ASCII grid

        self.gui = MainWindow()

        self.components = ComponentLibrary()
        self.symbol = Symbol()
        self.buffer = None

        all_components = [key for key in self.components.get_dict()]
        print("{0} libraries loaded, total number of components: {1}".format(self.components.nr_libraries(),
                                                                             self.components.nr_components()))
        # messages

        all_components.sort()
        pub.sendMessage('ALL_COMPONENTS', list=all_components)
        pub.sendMessage('GRID', grid=self.grid)

        # subscriptions

        pub.subscribe(self.on_component_changed, 'COMPONENT_CHANGED')
        pub.subscribe(self.on_rotate_symbol, 'ROTATE_SYMBOL')
        pub.subscribe(self.on_mirror_symbol, 'MIRROR_SYMBOL')
        pub.subscribe(self.on_paste_symbol, 'PASTE_SYMBOL')
        pub.subscribe(self.on_paste_line, 'PASTE_LINE')
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

        pub.subscribe(self.on_new, 'NEW_FILE')
        pub.subscribe(self.on_open, 'OPEN_FILE')
        pub.subscribe(self.on_save, 'SAVE_FILE')
        pub.subscribe(self.on_save_as, 'SAVE_AS_FILE')

        pub.subscribe(self.on_cut, 'CUT')
        pub.subscribe(self.on_copy, 'COPY')
        pub.subscribe(self.on_paste, 'PASTE')
        pub.subscribe(self.on_delete, 'DELETE')

        # open/save grid from/to file
        pub.subscribe(self.on_grid_from_file, 'GRID_FROM_FILE')
        pub.subscribe(self.on_grid_to_file, 'GRID_TO_FILE')

    def show_all(self):
        self.gui.show_all()

    def on_undo(self):
        self.grid.undo()
        pub.sendMessage('GRID', grid=self.grid)

    # File menu
    def on_new(self):
        print("Not yet implemented")

    def on_open(self):
        dialog = FileChooserWindow(open=True)

    def on_save(self):
        dialog = FileChooserWindow()

    def on_save_as(self):
        dialog = FileChooserWindow()

    # Edit menu

    def on_cut(self, pos, rect):
        self.buffer = self.grid.rect(pos, rect)
        self.grid.erase_rect(pos, rect)
        pub.sendMessage('NOTHING_SELECTED')

    def on_copy(self, pos, rect):
        grid = self.grid.rect(pos, rect)
        self.buffer = grid
        self.symbol = Symbol(grid)
        pub.sendMessage('SYMBOL_SELECTED', symbol=self.symbol)

    def on_paste(self, pos, rect):
        if self.buffer is not None:
            self.grid.fill_rect(pos, self.buffer)
        pub.sendMessage('NOTHING_SELECTED')

    def on_delete(self, pos, rect):
        self.grid.erase_rect(pos, rect)
        pub.sendMessage('NOTHING_SELECTED')

    # grid manipulation

    def on_insert_col(self, col):
        self.grid.insert_col(col)

    def on_insert_row(self, row):
        self.grid.insert_row(row)

    def on_remove_col(self, col):
        self.grid.remove_col(col)

    def on_remove_row(self, row):
        self.grid.remove_row(row)

    # component symbol

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

    # lines

    def on_paste_line(self, pos, dir, type, length):
        grid = self.symbol.line(dir, type, length)
        self.grid.fill_rect(pos, grid)

    # clipboard

    def on_copy_to_clipboard(self):
        self.grid.copy_to_clipboard()

    def on_paste_from_clipboard(self):
        self.grid.paste_from_clipboard()
        pub.sendMessage('GRID', grid=self.grid)

    def on_load_and_paste_from_clipboard(self):
        self.grid.load_and_paste_from_clipboard()
        pub.sendMessage('GRID', grid=self.grid)

    # file open/save

    def on_grid_to_file(self, filename):
        try:
            # open file in binary mode
            fout = open(filename, 'wb')
            str = self.grid.to_str()
            fout.write(str)
            fout.close()
        except IOError:
            print("Unable to open file for writing: %s" % filename)

    def on_grid_from_file(self, filename):
        try:
            # open file in binary mode
            file = open(filename, 'rb')
            str = file.read()

            self.grid.from_str(str)
            pub.sendMessage('GRID', grid=self.grid)

            file.close()

        except IOError:
            print("Unable to open file for reading: %s" % filename)
