"""
AACircuit.py
2020-03-02 JvO
"""

from pubsub import pub

from application import _
from application import COMPONENT, COL, ROW, RECT, LINE, MAG_LINE
from application.grid import Grid
from application.pos import Pos
from application.symbol import Symbol, Line
from application.symbol_view import SymbolView
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

        """
        <comp_command> ::= "comp:" <id> "," <orientation> "," <pos> "," <mirrored> "," <key>
        <other_command> ::= <type> ":" <id> "," <pos> ["," <pos>]
        <grid_command> ::= <grid> "," <row> | <col>

        <orientation> ::= { 0-3 }
        <mirrored> ::= "y" | "n"
        <type> ::= "char" | "line" | "rect" | "text"
        <grid> ::= "irow" | "icol" | "drow" | "dcol"

        <id> ::= <integer>
        <pos> ::= <x> "," <y>
        <key> ::= <string>
        <string> ::= '"' <alphanum>* '"'
        <x> ::= <integer>*
        <y> ::= <integer>*
        <row> ::= <integer>*
        <col> ::= <integer>*

        Example:
        COMP:45,0,10,15,N,"N-FET"
        COMP:46,0,10,15,N, "P-FET"
        LINE:10,10,15,10,20
        RECT:47,10,15,15,20
        CHAR:43,10,15
        TEXT:  + + Tekst + +,10,15
        TEXT:Tekst met komma,, in de tekst,10,15
        IROW:23
        DCOL:10
        """
        self.memo = []

        # all objects on the grid
        # [(position, object, view), ...] position in row/column coordinates
        self.objects = []

        # [(relative_position, object), ...] position relative to the selection rect (in row/column coordinates)
        self.selected_objects = []

        all_components = [key for key in self.components.get_dict()]
        if self.components.nr_libraries() == 1:
            print(_("One library loaded, total number of components: {0}").format(self.components.nr_components()))
        else:
            print(_("{0} libraries loaded, total number of components: {1}").format(self.components.nr_libraries(),
                                                                                    self.components.nr_components()))
        # messages

        # all_components.sort()
        pub.sendMessage('ALL_COMPONENTS', list=all_components)
        pub.sendMessage('GRID', grid=self.grid)

        # subscriptions

        pub.subscribe(self.on_character_changed, 'CHARACTER_CHANGED')
        pub.subscribe(self.on_component_changed, 'COMPONENT_CHANGED')

        pub.subscribe(self.on_rotate_symbol, 'ROTATE_SYMBOL')
        pub.subscribe(self.on_mirror_symbol, 'MIRROR_SYMBOL')
        pub.subscribe(self.on_paste_symbol, 'PASTE_SYMBOL')
        pub.subscribe(self.on_paste_objects, 'PASTE_OBJECTS')
        pub.subscribe(self.on_paste_line, 'PASTE_LINE')
        pub.subscribe(self.on_undo, 'UNDO')

        pub.subscribe(self.on_select_objects, 'SELECT_OBJECTS')

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
        pub.subscribe(self.on_read_from_file, 'READ_FROM_FILE')
        pub.subscribe(self.on_write_to_file, 'WRITE_TO_FILE')

    def show_all(self):
        self.gui.show_all()

    def on_undo(self):
        # TODO restore objects list
        self.grid.undo()
        pub.sendMessage('GRID', grid=self.grid)

    # File menu

    def on_new(self):
        self.grid = Grid(72, 36)
        pub.sendMessage('GRID', grid=self.grid)

    def on_open(self):
        dialog = FileChooserWindow(open=True)  # noqa: F841

    def on_save(self):
        if self.filename is not None:
            self.on_write_to_file(self.filename)

    def on_save_as(self):
        dialog = FileChooserWindow()  # noqa: F841

    # Edit menu

    # TODO cut|copy|paste and objects list maintenance, respectively remove from or add to the list

    def remove_from_objects(self, symbol):

        to_remove = []
        for idx, s in enumerate(self.objects):
            if id(s[1]) == id(symbol):
                to_remove.append(idx)

        for idx in to_remove:
            del self.objects[idx]

    def on_cut(self, pos, rect):

        self.find_selected(pos, rect)

        for obj in self.selected_objects:
            symbol_pos, symbol, symbol_view = obj
            self.remove_from_objects(symbol)

        self.buffer = self.grid.rect(pos, rect)
        self.grid.erase_rect(pos, rect)
        pub.sendMessage('NOTHING_SELECTED')

    def on_copy(self, pos, rect):
        """Select all symbols that are located within the selection rectangle."""

        self.find_selected(pos, rect)

        pub.sendMessage('OBJECTS_SELECTED', objects=self.selected_objects)

    def find_selected(self, pos, rect):
        """Select all symbols that are located within the selection rectangle."""

        ul = pos
        # rect = (width,height) in row/col dimension
        br = ul + Pos(rect[0], rect[1])
        rect = (ul, br)

        # select symbols of which the upper-left corner is within the selection rectangle
        selected = []
        for obj in self.objects:
            if obj[0].in_rect(rect):
                pos = obj[0]
                symbol = obj[1]
                relative_pos = pos - ul
                symbolview = SymbolView(symbol.grid)
                sel_obj = (relative_pos, symbol, symbolview)
                selected.append(sel_obj)

        self.selected_objects = selected

    def on_paste(self, pos, rect):
        if self.buffer is not None:
            self.grid.fill_rect(pos, self.buffer)
        pub.sendMessage('NOTHING_SELECTED')

    def on_delete(self, pos, rect):
        self.grid.erase_rect(pos, rect)
        pub.sendMessage('NOTHING_SELECTED')

    # grid manipulation

    def on_insert_col(self, col):
        str = "i{0}:{1}".format(COL, col)
        self.memo.append(str)
        self.grid.insert_col(col)

    def on_insert_row(self, row):
        str = "i{0}:{1}".format(ROW, row)
        self.memo.append(str)
        self.grid.insert_row(row)

    def on_remove_col(self, col):
        str = "d{0}:{1}".format(COL, col)
        self.memo.append(str)
        self.grid.remove_col(col)

    def on_remove_row(self, row):
        str = "d{0}:{1}".format(ROW, row)
        self.memo.append(str)
        self.grid.remove_row(row)

    # character/component symbol

    def on_character_changed(self, label):
        self.symbol = self.components.get_symbol(label)
        pub.sendMessage('CHARACTER_SELECTED', symbol=self.symbol)

    def on_component_changed(self, label):
        self.symbol = self.components.get_symbol(label)
        pub.sendMessage('SYMBOL_SELECTED', symbol=self.symbol)

    def on_rotate_symbol(self):
        self.symbol.grid_next()
        pub.sendMessage('SYMBOL_SELECTED', symbol=self.symbol)

    def on_mirror_symbol(self):
        self.symbol.mirror()
        pub.sendMessage('SYMBOL_SELECTED', symbol=self.symbol)

    def on_paste_symbol(self, pos):

        str = "{0}:{1},{2},{3}".format(COMPONENT, self.symbol.id, self.symbol.ori, pos)
        self.memo.append(str)

        symbol = self.symbol.copy()
        ref = (pos, symbol)
        self.objects.append(ref)

        self.grid.fill_rect(pos, self.symbol.grid)

    def on_paste_objects(self, pos):

        for obj in self.selected_objects:

            relative_pos, symbol, symbolview = obj
            target_pos = pos + relative_pos + Pos(0, 1)

            str = "{0}:{1},{2},{3}".format(COMPONENT, symbol.id, symbol.ori, target_pos)
            self.memo.append(str)

            ref = (target_pos, symbol)
            self.objects.append(ref)

            grid = symbol.grid
            self.grid.fill_rect(target_pos, grid)

        pub.sendMessage('NOTHING_SELECTED')

    def on_cut_objects(self, pos):

        for obj in self.selected_objects:

            # TODO remove symbol from the objects list

            pos, symbol = obj

            grid = symbol.grid
            dummy, rect = grid.rect()

            self.grid.erase_rect(pos, rect)

        pub.sendMessage('NOTHING_SELECTED')

    # lines

    def on_paste_line(self, startpos, endpos, type):

        str = "{0}:{1},{2},{3}".format(LINE, type, startpos, endpos)
        self.memo.append(str)

        self.symbol = Line(startpos, endpos, type)
        ref = (startpos, self.symbol)
        self.objects.append(ref)

        self.grid.fill_rect(startpos, self.symbol.grid)

    # clipboard

    def on_copy_to_clipboard(self):
        self.grid.copy_to_clipboard()

    def on_paste_from_clipboard(self):
        self.grid.paste_from_clipboard()
        pub.sendMessage('GRID', grid=self.grid)

    def on_load_and_paste_from_clipboard(self):
        self.grid.load_and_paste_from_clipboard()
        pub.sendMessage('GRID', grid=self.grid)

    # other

    def on_select_objects(self):
        pub.sendMessage('SELECTING_OBJECTS', objects=self.objects)

    # file open/save

    def on_write_to_file(self, filename):
        try:
            fout = open(filename, 'w')

            str = ""
            for line in self.memo:
                print("memo:{0}".format(line))
                str += line + "\n"
            fout.write(str)

            fout.close()
        except IOError:
            print(_("Unable to open file for writing: %s" % filename))

    def on_read_from_file(self, filename):
        self.filename = filename
        try:
            # open file in binary mode
            file = open(filename, 'rb')
            str = file.read()

            self.grid.from_str(str)
            pub.sendMessage('GRID', grid=self.grid)
            pub.sendMessage('FILE_OPENED')

            file.close()

        except IOError:
            print(_("Unable to open file for reading: %s" % filename))
