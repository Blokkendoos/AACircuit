"""
AACircuit.py
2020-03-02 JvO
"""

import os
import re
import json
import xerox
import collections
from pubsub import pub

from application import gettext as _
from application import ERROR, WARNING
from application import REMOVE, INSERT
from application import ERASER, COMPONENT, CHARACTER, TEXT, COL, ROW, DRAW_RECT, ARROW, LINE, MAG_LINE, DIR_LINE
from application.pos import Pos
from application.grid import Grid
from application.magic_line_settings import MagicLineSettings
from application.preferences import Preferences
from application.main_window import MainWindow
from application.memo_editing import MemoEditingDialog
from application.component_library import ComponentLibrary
from application.file import InputFileChooser, InputFileAscii, OutputFileChooser, OutputFileAscii, OutputFilePDF, PrintOperation
from application.symbol import Eraser, Character, Text, Line, MagLine, MagLineOld, DirLine, Rect, Arrow, Row, Column

SelectedObjects = collections.namedtuple('SelectedObjects', ['startpos', 'symbol'])
Action = collections.namedtuple('Action', ['action', 'symbol'])


class Controller(object):

    def __init__(self):
        self.prefs = Preferences()
        self.ml_settings = MagicLineSettings()
        self.gui = MainWindow()
        self.complib = ComponentLibrary()
        self.filename = None

        self.init_stack()
        self.init_grid()

        # True: read original (Delphi/Pascal) AACircuit file
        self._import_legacy = False

        all_components = [key for key in self.complib.components]
        if self.complib.nr_libraries() == 1:
            msg = _("One library loaded, total number of components: {0}").format(self.complib.nr_components())
        else:
            msg = _("{0} libraries loaded, total number of components: {1}").format(self.complib.nr_libraries(),
                                                                                    self.complib.nr_components())
        pub.sendMessage('STATUS_MESSAGE', msg=msg)
        pub.sendMessage('ALL_COMPONENTS', list=all_components)

        # subscriptions

        pub.subscribe(self.on_character_changed, 'CHARACTER_CHANGED')
        pub.subscribe(self.on_component_changed, 'COMPONENT_CHANGED')

        pub.subscribe(self.on_rotate_symbol, 'ROTATE_SYMBOL')
        pub.subscribe(self.on_mirror_symbol, 'MIRROR_SYMBOL')

        pub.subscribe(self.on_paste_objects, 'PASTE_OBJECTS')
        pub.subscribe(self.on_paste_mag_line, 'PASTE_MAG_LINE')
        pub.subscribe(self.on_paste_dir_line, 'PASTE_DIR_LINE')
        pub.subscribe(self.on_paste_line, 'PASTE_LINE')
        pub.subscribe(self.on_paste_rect, 'PASTE_RECT')
        pub.subscribe(self.on_paste_arrow, 'PASTE_ARROW')
        pub.subscribe(self.on_paste_text, 'PASTE_TEXT')
        pub.subscribe(self.on_paste_text, 'PASTE_TEXTBLOCK')
        pub.subscribe(self.on_undo, 'UNDO')
        pub.subscribe(self.on_redo, 'REDO')

        pub.subscribe(self.on_erase, 'ERASE')
        pub.subscribe(self.on_eraser_selected, 'ERASER')
        pub.subscribe(self.on_select_rect, 'SELECT_RECT')
        pub.subscribe(self.on_select_object, 'SELECT_OBJECT')
        pub.subscribe(self.on_selector_moved, 'SELECTOR_MOVED')

        # insert/remove rows or columns
        pub.subscribe(self.on_grid_col, 'GRID_COL')
        pub.subscribe(self.on_grid_row, 'GRID_ROW')

        # clipboard
        pub.subscribe(self.on_cut, 'CUT')
        pub.subscribe(self.on_copy, 'COPY')

        pub.subscribe(self.on_copy_grid, 'COPY_GRID')
        pub.subscribe(self.on_paste_grid, 'PASTE_GRID')
        pub.subscribe(self.on_load_and_paste_grid, 'LOAD_AND_PASTE_GRID')
        pub.subscribe(self.on_load_ascii_from_file, 'LOAD_ASCII_FROM_FILE')

        pub.subscribe(self.on_edit_memo, 'EDIT_MEMO')
        pub.subscribe(self.on_rerun_memo, 'RERUN_MEMO')

        # file
        pub.subscribe(self.on_new, 'NEW_FILE')
        pub.subscribe(self.on_open, 'OPEN_FILE')
        pub.subscribe(self.on_save, 'SAVE_FILE')
        pub.subscribe(self.on_save_as, 'SAVE_AS_FILE')
        pub.subscribe(self.on_import_aacircuit, 'IMPORT_AACIRCUIT')
        pub.subscribe(self.on_export_as_pdf, 'EXPORT_AS_PDF')
        pub.subscribe(self.on_export_as_ascii, 'EXPORT_AS_ASCII')

        # pub.subscribe(self.on_begin_print, 'BEGIN_PRINT')
        pub.subscribe(self.on_print_file, 'PRINT_FILE')
        pub.subscribe(self.on_end_print, 'END_PRINT')

        # open/save grid from/to file
        pub.subscribe(self.on_read_from_file, 'READ_FROM_FILE')
        pub.subscribe(self.on_write_to_file, 'WRITE_TO_FILE')
        pub.subscribe(self.on_write_to_ascii_file, 'WRITE_TO_ASCII_FILE')

        # grid
        pub.subscribe(self.on_grid_size, 'GRID_SIZE')
        pub.subscribe(self.on_redraw_grid, 'REDRAW_GRID')

    @property
    def legacy(self):
        return self._import_legacy

    @legacy.setter
    def legacy(self, value):
        self._import_legacy = value

    def init_stack(self):
        # action stack with the last cut/pasted symbol(s)
        self.latest_action = []
        # redo stack that contains the last undone actions
        self.undone_action = []
        # all objects on the grid
        self.objects = []
        self.selected_objects = []

    def init_grid(self, cols=None, rows=None):
        if cols is None:
            self._cols = Preferences.values['DEFAULT_COLS']
        else:
            self._cols = cols
        if rows is None:
            self._rows = Preferences.values['DEFAULT_ROWS']
        else:
            self._rows = rows
        self.grid = Grid(self._cols, self._rows)
        pub.sendMessage('NEW_GRID', grid=self.grid)

    def cell_callback(self, pos):
        # prevent calling an old grid instance method
        # FIXME better solution (than that this controller needs to know about a grid method)?
        return self.grid.cell(pos)

    def show_all(self):
        # DEBUG
        # self._import_legacy = True
        # self.on_read_from_file('tests/files/original_741.aac')
        # self.on_read_from_file('tests/files/original_JKMasterSlave.aac')
        self.gui.show_all()

    def revert_action(self, stack):

        def cut_symbol():
            self.remove_from_objects(symbol)
            symbol.remove(self.grid)

        def paste_symbol():
            self.objects.append(symbol)
            symbol.paste(self.grid)

        action = None
        symbol = None
        if len(stack) > 0:
            action, symbol = stack.pop()
            # revert action
            if action == REMOVE:
                paste_symbol()
                action = INSERT
            elif action == INSERT:
                cut_symbol()
                action = REMOVE
        return symbol, action

    def on_undo(self):
        if len(self.latest_action) > 0:
            symbol, action = self.revert_action(self.latest_action)
            if action:
                self.push_undone(symbol, action)
        if len(self.latest_action) < 1:
            # there are no more actions to undo
            pub.sendMessage('UNDO_CHANGED', undo=False)

    def on_redo(self):
        if len(self.undone_action) > 0:
            symbol, action = self.revert_action(self.undone_action)
            if action:
                self.push_latest_action(symbol, action)
        if len(self.undone_action) < 1:
            # there are no more actions to redo
            pub.sendMessage('REDO_CHANGED', redo=False)

    def push_latest_action(self, symbol, action=INSERT):
        """Add a cut or paste action to the undo stack."""
        act = Action(action=action, symbol=symbol)
        self.latest_action.append(act)
        pub.sendMessage('UNDO_CHANGED', undo=True)

    def push_undone(self, symbol, action):
        """Add an undone action to the redo stack."""
        act = Action(action=action, symbol=symbol)
        self.undone_action.append(act)
        pub.sendMessage('REDO_CHANGED', redo=True)

    def add_selected_object(self, symbol):
        obj = SelectedObjects(symbol.startpos, symbol)
        self.selected_objects.append(obj)

    # File menu

    def on_new(self):
        self.init_grid()
        self.init_stack()
        self.filename = None
        pub.sendMessage('NOTHING_SELECTED')

    def on_open(self):
        self._import_legacy = False
        dialog = InputFileChooser()  # noqa: F841

    def on_save(self):
        if self.filename is not None:
            self.on_write_to_file(self.filename)

    def on_save_as(self):
        dialog = OutputFileChooser()  # noqa: F841

    def on_import_aacircuit(self):
        self._import_legacy = True
        dialog = InputFileChooser()  # noqa: F841

    def on_export_as_pdf(self, filename=None):
        if filename is None:
            if self.filename is None:
                filename = _("Untitled.pdf")
            else:
                filename = os.path.splitext(os.path.basename(self.filename))[0] + '.pdf'
        dialog = OutputFilePDF(filename)  # noqa: F841

    def on_export_as_ascii(self, filename=None):
        if filename is None:
            if self.filename is None:
                filename = _("Untitled_schema.txt")
            else:
                filename = os.path.splitext(os.path.basename(self.filename))[0] + '.txt'
        dialog = OutputFileAscii(filename)  # noqa: F841

    def on_end_print(self):
        msg = _("Finished printing")
        pub.sendMessage('STATUS_MESSAGE', msg=msg)

    def on_print_file(self):
        dialog = PrintOperation()  # noqa: F841
        dialog.run()

    # Edit menu

    def remove_from_objects(self, symbol):
        for idx, sym in enumerate(self.objects):
            # the id's differ as instances are copied before being added to the selection list
            # if id(sym) == id(symbol):
            if sym.startpos == symbol.startpos and sym.id == symbol.id:
                del self.objects[idx]
                break

    def find_selected(self, rect):
        """Find all symbols that are located within the selection rectangle."""
        ul, br = rect
        selected = []
        for symbol in self.objects:
            # select symbols of which the upper-left corner is within the selection rectangle
            if symbol.pickpoint_pos.in_rect(rect):
                copy = symbol.copy()
                selection = SelectedObjects(startpos=ul, symbol=copy)
                selected.append(selection)

        # TODO Only one of multiple objects sharing the same position will be selected
        if len(selected) > 0:
            selected.sort(key=lambda x: x.startpos)
            selected_unique = []
            pps = set()
            for sel in selected:
                if sel.symbol.pickpoint_pos in pps:
                    msg = _("More than one item at position: {} !").format(sel.symbol.pickpoint_pos)
                    pub.sendMessage('STATUS_MESSAGE', msg=msg, type=WARNING)
                else:
                    pps.add(sel.symbol.pickpoint_pos)
                    selected_unique.append(sel)
            selected = selected_unique
        self.selected_objects = selected

    def on_selector_moved(self, pos):
        """Show the object (type) that is located at the cursor position."""
        count = 0
        for symbol in self.objects:
            if symbol.pickpoint_pos == pos:
                last_found = symbol
                count += 1
        if count > 1:
            msg = _("More than one item at position: {} !").format(pos)
            pub.sendMessage('STATUS_MESSAGE', msg=msg, type=WARNING)
        elif count == 1:
            msg = "Object: " + last_found.name
            pub.sendMessage('STATUS_MESSAGE', msg=msg)
        else:
            pub.sendMessage('STATUS_MESSAGE', msg="")

    def on_cut(self, rect):
        self.find_selected(rect)
        action = []
        for obj in self.selected_objects:
            act = Action(action=REMOVE, symbol=obj.symbol)
            action.append(act)
            obj.symbol.remove(self.grid)
            self.remove_from_objects(obj.symbol)
        self.latest_action += action
        pub.sendMessage('UNDO_CHANGED', undo=True)
        pub.sendMessage('OBJECTS_SELECTED', objects=self.selected_objects)
        if len(self.selected_objects) > 0:
            first_obj = self.selected_objects[0]
            pub.sendMessage('ORIENTATION_CHANGED', ori=first_obj.symbol.ori_as_str)

    def on_copy(self, rect):
        """Select all symbols that are located within the selection rectangle."""
        self.find_selected(rect)
        pub.sendMessage('OBJECTS_SELECTED', objects=self.selected_objects)
        if len(self.selected_objects) > 0:
            first_obj = self.selected_objects[0]
            pub.sendMessage('ORIENTATION_CHANGED', ori=first_obj.symbol.ori_as_str)

    def on_edit_memo(self):
        memo = ""
        for symbol in self.objects:
            memo += symbol.memo() + '\n'
        dialog = MemoEditingDialog(memo)
        dialog.run()
        dialog.hide()

    def on_rerun_memo(self, str):
        self.init_stack()
        self.init_grid()
        memo = []
        str = str.splitlines()
        for line in str:
            memo.append(line)
        self.play_memo(memo)

    # grid manipulation

    def on_grid_size(self, cols, rows):
        self._rows = rows
        self._cols = cols
        self.on_redraw_grid()

    def on_redraw_grid(self):
        rows = self._rows
        cols = self._cols
        self.init_grid(cols, rows)
        for symbol in self.objects:
            symbol.paste(self.grid)

    def on_grid_col(self, col, action):
        # don't mistake the symbol action for the edit action
        symbol = Column(col, action)
        self.objects.append(symbol)
        symbol.paste(self.grid)
        self.push_latest_action(symbol)

    def on_grid_row(self, row, action):
        # don't mistake the symbol action for the edit action
        symbol = Row(row, action)
        self.objects.append(symbol)
        symbol.paste(self.grid)
        self.push_latest_action(symbol)

    # character/component symbol

    def on_character_changed(self, char):
        symbol = Character(char)
        self.selected_objects = []
        self.add_selected_object(symbol)
        pub.sendMessage('CHARACTER_SELECTED', char=symbol)

    def on_component_changed(self, label):
        symbol = self.complib.get_symbol(label)
        self.selected_objects = []
        self.add_selected_object(symbol)
        pub.sendMessage('STATUS_MESSAGE', msg='')
        pub.sendMessage('SYMBOL_SELECTED', symbol=symbol)
        pub.sendMessage('ORIENTATION_CHANGED', ori=symbol.ori_as_str)

    def on_rotate_symbol(self):
        first = True
        for obj in self.selected_objects:
            obj.symbol.rotate()
            # show the orientation of a single, or the first, symbol in the statusbar
            if first:
                first = False
                pub.sendMessage('ORIENTATION_CHANGED', ori=obj.symbol.ori_as_str)

    def on_mirror_symbol(self):
        for obj in self.selected_objects:
            obj.symbol.mirrored = 1 - obj.symbol.mirrored  # toggle 0/1

    def on_paste_text(self, symbol):
        self.paste_symbol(symbol)
        pub.sendMessage('UNDO_CHANGED', undo=True)

    def on_paste_objects(self, pos):
        """
        Paste selection.
        :param pos: the target position in grid (col, row) coordinates.
        """
        action = []
        for obj in self.selected_objects:
            offset = pos - obj.startpos
            # TODO make the position translation a Symbol method?
            symbol = obj.symbol.copy()
            symbol.startpos += offset
            symbol.endpos += offset
            act = Action(action=INSERT, symbol=symbol)
            action.append(act)
            self.objects.append(symbol)
            symbol.paste(self.grid)
        self.latest_action += action
        pub.sendMessage('UNDO_CHANGED', undo=True)

    def paste_symbol(self, symbol):
        self.selected_objects = []
        self.add_selected_object(symbol)
        self.objects.append(symbol)
        symbol.paste(self.grid)
        self.push_latest_action(symbol)

    # lines

    def on_paste_line(self, startpos, endpos, type):
        symbol = Line(startpos, endpos, type)
        self.paste_symbol(symbol)

    def on_paste_dir_line(self, startpos, endpos):
        symbol = DirLine(startpos, endpos)
        self.paste_symbol(symbol)

    def on_paste_mag_line(self, startpos, endpos):
        symbol = MagLine(startpos, endpos, self.cell_callback)
        # symbol = MagLineOld(startpos, endpos, self.cell_callback)
        self.paste_symbol(symbol)

    def on_paste_mag_line_w_type(self, startpos, endpos, type):
        # backward compatibility
        if type == 1:
            symbol = MagLine(startpos, endpos, self.cell_callback)
        else:
            symbol = MagLineOld(startpos, endpos, self.cell_callback)
        self.paste_symbol(symbol)

    def on_paste_rect(self, startpos, endpos):
        symbol = Rect(startpos, endpos)
        self.paste_symbol(symbol)

    def on_paste_arrow(self, startpos, endpos):
        symbol = Arrow(startpos, endpos)
        self.paste_symbol(symbol)

    # clipboard

    def on_copy_grid(self):
        """
        Copy the content of the grid to the clipboard.
        The rows are copied as ASCII lines, terminated by CR.
        """
        xerox.copy(self.grid.content_as_str())

    def on_paste_grid(self):
        """
        Copy the content of the clipboard to the grid.
        ASCII lines, terminated by CR, are interpreted as rows.
        """
        selected = []
        pos = Pos(0, 0)
        relative_pos = Pos(0, 0)
        content = xerox.paste().splitlines()
        for line in content:
            symbol = Text(relative_pos, line)
            selection = SelectedObjects(startpos=pos, symbol=symbol)
            selected.append(selection)
            relative_pos += Pos(0, 1)
        self.selected_objects = selected
        pub.sendMessage('OBJECTS_SELECTED', objects=self.selected_objects)

    def on_load_and_paste_grid(self):
        self.selected_objects = []
        dialog = InputFileAscii()  # noqa: F841

    def on_load_ascii_from_file(self, filename):
        try:
            file = open(filename, 'r')
            str = file.readlines()
            startpos = Pos(0, 0)
            pos = Pos(0, 0)
            for line in str:
                # create a TEXT instance for each line
                # fill selected_objects...
                symbol = Text(pos, line)
                selection = SelectedObjects(startpos=startpos, symbol=symbol)
                pos += Pos(0, 1)
                self.selected_objects.append(selection)
            file.close()
            pub.sendMessage('OBJECTS_SELECTED', objects=self.selected_objects)
            return True

        except IOError as e:
            msg = _("Unable to open file for reading: {} error({}): {}").format(filename, e.errno, e.strerror)
            pub.sendMessage('STATUS_MESSAGE', msg=msg, type=WARNING)
            return False

        except UnicodeDecodeError as e:
            msg = _("Unable to open file for reading: {} error({}): {}").format(filename, e.encoding, e.reason)
            pub.sendMessage('STATUS_MESSAGE', msg=msg, type=WARNING)
            return False

    # other

    def on_erase(self, startpos, size):
        """Erase an area of the given size."""
        symbol = Eraser(size, startpos)
        self.selected_objects = []
        self.add_selected_object(symbol)
        self.objects.append(symbol)
        symbol.paste(self.grid)
        self.push_latest_action(symbol)
        pub.sendMessage('UNDO_CHANGED', undo=True)

    def on_eraser_selected(self, size):
        """Select eraser of the given size."""
        symbol = Eraser(size)
        self.selected_objects = []
        self.add_selected_object(symbol)
        pub.sendMessage('SYMBOL_SELECTED', symbol=symbol)

    def select_all_objects(self):
        """Select all objects."""
        selection = []
        for symbol in self.objects:
            sel = SelectedObjects(symbol.startpos, symbol)
            selection.append(sel)
        return selection

    def on_select_rect(self):
        """Select multiple objects."""
        pub.sendMessage('NOTHING_SELECTED')
        pub.sendMessage('SELECTING_RECT', objects=self.select_all_objects())
        msg = _("Selecting rectangle...")
        pub.sendMessage('STATUS_MESSAGE', msg=msg)

    def on_select_object(self):
        """Select individual objects."""
        pub.sendMessage('NOTHING_SELECTED')
        pub.sendMessage('SELECTING_OBJECT', objects=self.select_all_objects())

    # file open/save

    # TODO naar eigen file of class zetten

    def on_write_to_file(self, filename):
        try:
            fout = open(filename, 'w')
            str = ""
            for symbol in self.objects:
                str += symbol.memo() + "\n"
            fout.write(str)
            fout.close()
            self.filename = filename
            msg = _("Schema has been saved in: {}").format(filename)
            pub.sendMessage('STATUS_MESSAGE', msg=msg)
            # in case we have saved a new file, we now have an opened file
            pub.sendMessage('FILE_OPENED')
            return True

        except IOError:
            msg = _("Unable to open file for writing: {}").format(filename)
            pub.sendMessage('STATUS_MESSAGE', msg=msg, type=ERROR)
            return False

    def on_write_to_ascii_file(self, filename):
        try:
            fout = open(filename, 'w')
            str = self.grid.content_as_str()
            fout.write(str)
            fout.close()
            self.filename = filename
            msg = _("ASCII Schema has been saved in: {}").format(filename)
            pub.sendMessage('STATUS_MESSAGE', msg=msg)
            return True

        except IOError:
            msg = _("Unable to open file for writing: %s" % filename)
            pub.sendMessage('STATUS_MESSAGE', msg=msg, type=ERROR)
            return False

    def on_read_from_file(self, filename):
        self.filename = filename
        try:
            file = open(filename, 'r')
            str = file.readlines()
            # start with a fresh grid
            self.init_stack()
            self.init_grid()
            memo = []
            for line in str:
                memo.append(line)
            file.close()

            if self._import_legacy:
                skipped = self.play_memo_original_aac(memo)
            else:
                skipped = self.play_memo(memo)

            # empty the undo stack (from the played memo actions)
            # self.latest_action = []
            # pub.sendMessage('UNDO_CHANGED', undo=False)

            # TODO only the basename in statusbar, or truncated path, e.g. when the full path exceeds length x
            base = os.path.basename(filename)
            if skipped > 0:
                msg = _("{0} lines skipped in: {1}").format(skipped, base)
            else:
                msg = _("File: {}").format(base)

            pub.sendMessage('STATUS_MESSAGE', msg=msg)
            pub.sendMessage('FILE_OPENED')
            pub.sendMessage('NOTHING_SELECTED')
            return True

        except IOError as e:
            msg = _("Unable to open file for reading: {} error({}): {}").format(filename, e.errno, e.strerror)
            pub.sendMessage('STATUS_MESSAGE', msg=msg, type=ERROR)
            return False

        except UnicodeDecodeError as e:
            msg = _("Unable to open file for reading: {} error({}): {}").format(filename, e.encoding, e.reason)
            pub.sendMessage('STATUS_MESSAGE', msg=msg, type=ERROR)
            return False

    def play_memo(self, memo):

        def play_m1(m):
            skip = 0
            type = m.group(1)
            if type == ERASER:
                w = int(m.group(2))
                h = int(m.group(3))
                size = (w, h)
                x, y = m.group(4, 5)
                pos = Pos(x, y)
                symbol = Eraser(size)
                self.selected_objects = []
                self.add_selected_object(symbol)
                self.on_paste_objects(pos)

            elif type == COMPONENT:
                id = int(m.group(2))
                orientation = int(m.group(3))
                mirrored = int(m.group(4))
                x, y = m.group(5, 6)
                pos = Pos(x, y)
                symbol = self.complib.get_symbol_byid(id)
                symbol.ori = orientation
                symbol.mirrored = mirrored
                self.selected_objects = []
                self.add_selected_object(symbol)
                self.on_paste_objects(pos)

            elif type == CHARACTER:
                ascii = m.group(2)
                char = chr(int(ascii))
                x, y = m.group(3, 4)
                pos = Pos(x, y)
                symbol = Character(char)
                self.selected_objects = []
                self.add_selected_object(symbol)
                self.on_paste_objects(pos)

            elif type == LINE:
                line_type = int(m.group(2))
                x, y = m.group(3, 4)
                startpos = Pos(x, y)
                x, y = m.group(5, 6)
                endpos = Pos(x, y)
                self.on_paste_line(startpos, endpos, line_type)

            elif type == DIR_LINE:
                x, y = m.group(2, 3)
                startpos = Pos(x, y)
                x, y = m.group(4, 5)
                endpos = Pos(x, y)
                self.on_paste_dir_line(startpos, endpos)

            elif type == MAG_LINE:
                line_type = int(m.group(2))
                x, y = m.group(3, 4)
                startpos = Pos(x, y)
                x, y = m.group(5, 6)
                endpos = Pos(x, y)
                self.on_paste_mag_line_w_type(startpos, endpos, line_type)

            elif type == DRAW_RECT:
                x, y = m.group(2, 3)
                startpos = Pos(x, y)
                x, y = m.group(4, 5)
                endpos = Pos(x, y)
                self.on_paste_rect(startpos, endpos)

            elif type == ARROW:
                x, y = m.group(2, 3)
                startpos = Pos(x, y)
                x, y = m.group(4, 5)
                endpos = Pos(x, y)
                self.on_paste_arrow(startpos, endpos)
            else:
                skip = 1
            return skip

        def play_m2(m):
            skip = 0
            type = m.group(1)
            if type == 'i':
                action = INSERT
            else:
                action = REMOVE
            what = m.group(2)
            nr = int(m.group(3))
            if what == COL:
                self.on_grid_col(nr, action)
            elif what == ROW:
                self.on_grid_row(nr, action)
            else:
                skip = 1
            return skip

        def play_m3(m):
            skip = 0
            type = m.group(1)
            if type == TEXT:
                orientation = int(m.group(2))
                x, y = m.group(3, 4)
                pos = Pos(x, y)
                str = m.group(5)
                text = json.loads(str)
                symbol = Text(pos, text, orientation)
                self.selected_objects = []
                self.add_selected_object(symbol)
                self.on_paste_objects(pos)
            else:
                skip = 1
            return skip

        skipped = 0
        linenr = 0
        for item in memo:
            linenr += 1
            m1 = re.search('(^eras|^comp|^char|^rect|^line|^magl|^dirl|^arrw):(\d+),(\d+),(\d+),?(\d*),?(\d*),?(\d*)', item)  # noqa W605
            m2 = re.search('(^d|^i)(row|col):(\d+)', item)  # noqa W605
            m3 = re.search('(^text):(\d+),(\d+),(\d+),(.*)', item)  # noqa W605
            if m1 is not None:
                skipped += play_m1(m1)
            elif m2 is not None:
                skipped += play_m2(m2)
            elif m3 is not None:
                skipped += play_m3(m3)
            else:
                msg = _("skipped linenr: {}").format(linenr)
                pub.sendMessage('STATUS_MESSAGE', msg=msg, type=WARNING)
                skipped += 1
        return skipped

    def play_memo_original_aac(self, memo):

        def play_m1(m):
            skip = 0
            component = m.group(1)
            type = component.lower()
            if type == ERASER:
                w = int(m.group(2))
                h = int(m.group(3))
                size = (w, h)
                x, y = m.group(4, 5)
                pos = Pos(x, y)
                symbol = Eraser(size)
                self.selected_objects = []
                self.add_selected_object(symbol)
                self.on_paste_objects(pos)

            elif type == COMPONENT:
                id = int(m.group(2))
                orientation = int(m.group(3))
                mirrored = int(m.group(4))
                x, y = m.group(5, 6)
                pos = Pos(x, y)
                symbol = self.complib.get_symbol_byid(id)
                symbol.ori = orientation
                symbol.mirrored = mirrored
                self.selected_objects = []
                self.add_selected_object(symbol)
                self.on_paste_objects(pos)

            elif type == CHARACTER:
                ascii = m.group(2)
                char = chr(int(ascii))
                x, y = m.group(3, 4)
                pos = Pos(x, y)
                symbol = Character(char)
                self.selected_objects = []
                self.add_selected_object(symbol)
                self.on_paste_objects(pos)

            elif type == LINE:
                terminal = int(m.group(2))
                x, y = m.group(3, 4)
                startpos = Pos(x, y)
                x, y = m.group(5, 6)
                endpos = Pos(x, y)
                self.on_paste_line(startpos, endpos, terminal)

            elif type == DIR_LINE:
                x, y = m.group(2, 3)
                startpos = Pos(x, y)
                x, y = m.group(4, 5)
                endpos = Pos(x, y)
                self.on_paste_dir_line(startpos, endpos)

            elif type == MAG_LINE:
                line_type = int(m.group(2))

                x, y = m.group(3, 4)
                startpos = Pos(x, y)
                x, y = m.group(5, 6)
                endpos = Pos(x, y)
                self.on_paste_mag_line_w_type(startpos, endpos, line_type)

            elif type == DRAW_RECT:
                x, y = m.group(3, 4)
                startpos = Pos(x, y)
                x, y = m.group(5, 6)
                endpos = Pos(x, y)
                self.on_paste_rect(startpos, endpos)
            else:
                msg = _("skipped: {}").format(type)
                pub.sendMessage('STATUS_MESSAGE', msg=msg, type=WARNING)
                skip = 1
            return skip

        def play_m2(m):
            type = m.group(1)
            if type == 'I':
                action = INSERT
            else:
                action = REMOVE
            what = m.group(2)
            nr = int(m.group(3))
            if what.lower() == COL:
                symbol = Column(nr, action)
            elif what.lower() == ROW:
                symbol = Row(nr, action)
            self.selected_objects = []
            self.add_selected_object(symbol)
            self.on_paste_objects(symbol.startpos)
            return 0

        def play_m3(m):
            skip = 0
            type = m.group(1)
            if type == TEXT:
                text = m.group(2)
                x, y = m.group(3, 4)
                pos = Pos(x, y)
                orientation = 0
                symbol = Text(pos, text, orientation)
                self.selected_objects = []
                self.add_selected_object(symbol)
                self.on_paste_objects(pos)
            else:
                msg = _("skipped: {}").format(type)
                pub.sendMessage('STATUS_MESSAGE', msg=msg, type=WARNING)
                skip = 1
            return skip

        def play_m4(m):
            id = int(m.group(2))
            orientation = int(m.group(3))
            orientation -= 1
            x, y = m.group(4, 5)
            pos = Pos(x, y)
            if m.group(6) == 's':
                mirrored = 1
            else:
                mirrored = 0
            symbol = self.complib.get_symbol_byid(id)
            symbol.ori = orientation
            symbol.mirrored = mirrored
            self.selected_objects = []
            self.add_selected_object(symbol)
            self.on_paste_objects(pos)
            return 0

        skipped = 0
        linenr = 0
        for item in memo:
            linenr += 1
            m1 = re.search('(^eras|^char|^rect|^line|^MagL|^dirl):(\d+),(\d+),(\d+),?(\d*),?(\d*),?(\d*)', item)  # noqa W605
            m2 = re.search('(^D|^I)(ROW|COL):(\d+)', item)  # noqa W605
            m3 = re.search('(^text):(.+),(\d+),(\d+)', item)  # noqa W605
            m4 = re.search('(^comp):(\d+),(\d+),(\d+),(\d+),(\w),?(\w*)', item)  # noqa W605
            if m1 is not None:
                skipped += play_m1(m1)
            elif m2 is not None:
                skipped += play_m2(m2)
            elif m3 is not None:
                skipped += play_m3(m3)
            elif m4 is not None:
                skipped += play_m4(m4)
            else:
                msg = _("skipped linenr: {}").format(linenr)
                pub.sendMessage('STATUS_MESSAGE', msg=msg, type=WARNING)
                skipped += 1
        return skipped
