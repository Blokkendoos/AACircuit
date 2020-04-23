"""
AACircuit
2020-03-02 JvO
"""

from pubsub import pub

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402


class MenuBar(object):

    def __init__(self, builder, grid_view):

        self.grid_view = grid_view

        # file menu
        menu_new = builder.get_object('new_file')
        menu_open = builder.get_object('open_file')
        self.menu_save = builder.get_object('save_file')
        self.menu_save_as = builder.get_object('save_as_file')
        self.menu_print_file = builder.get_object('print_file')

        menu_new.connect('activate', self.on_menu_file)
        menu_open.connect('activate', self.on_menu_file)
        self.menu_save.connect('activate', self.on_menu_file)
        self.menu_save_as.connect('activate', self.on_menu_file)
        self.menu_print_file.connect('activate', self.on_menu_file)

        self.menu_save.set_sensitive(False)

        # edit menu
        self.menu_copy = builder.get_object('copy')
        self.menu_cut = builder.get_object('cut')
        self.menu_paste = builder.get_object('paste')
        self.menu_undo = builder.get_object('undo')
        self.menu_redo = builder.get_object('redo')

        self.menu_copy.connect('activate', self.on_menu_edit)
        self.menu_cut.connect('activate', self.on_menu_edit)
        self.menu_paste.connect('activate', self.on_menu_edit)
        self.menu_undo.connect('activate', self.on_undo)
        self.menu_redo.connect('activate', self.on_undo)

        self.menu_copy.set_sensitive(False)
        self.menu_cut.set_sensitive(False)
        self.menu_paste.set_sensitive(False)
        self.menu_undo.set_sensitive(False)
        self.menu_redo.set_sensitive(False)

        self.menu_grid = [
            builder.get_object('menu_copy_grid'),
            builder.get_object('menu_paste_grid'),
            builder.get_object('menu_load_and_paste_grid')]
        for option in self.menu_grid:
            option.connect('activate', self.on_menu_grid)

        # symbol menu
        self.menu_rotate = builder.get_object('rotate_symbol')
        self.menu_mirror = builder.get_object('mirror_symbol')

        self.menu_rotate.connect('activate', self.on_menu_symbol)
        self.menu_mirror.connect('activate', self.on_menu_symbol)

        self.menu_rotate.set_sensitive(False)
        self.menu_mirror.set_sensitive(False)

        # view menu
        self.menu_grid_size = [
            builder.get_object('grid_size_1'),
            builder.get_object('grid_size_2'),
            builder.get_object('grid_size_3'),
            builder.get_object('grid_size_4')]
        for option in self.menu_grid_size:
            option.connect('activate', self.on_menu_grid_size)

        pub.subscribe(self.on_file_opened, 'FILE_OPENED')
        pub.subscribe(self.on_nothing_selected, 'NOTHING_SELECTED')
        pub.subscribe(self.on_symbol_selected, 'SYMBOL_SELECTED')
        pub.subscribe(self.on_selection_changed, 'SELECTION_CHANGED')
        pub.subscribe(self.on_undo_changed, 'UNDO_CHANGED')
        pub.subscribe(self.on_redo_changed, 'REDO_CHANGED')

    def on_menu_file(self, item):
        name = Gtk.Buildable.get_name(item).upper()
        pub.sendMessage(name)

    def on_file_opened(self):
        # enable File menu 'save' when a file has been opened
        self.menu_save.set_sensitive(True)

    def on_menu_edit(self, item):
        # menu cut|copy|paste
        name = Gtk.Buildable.get_name(item)

        # get the rectangle (ul and br have been set in drag begin/end)
        ul, br = self.grid_view.drag_rect

        pub.sendMessage(name.upper(), rect=(ul, br))

    def on_menu_grid(self, button):
        name = Gtk.Buildable.get_name(button)
        # strip prefix
        name = name.replace('menu_', '')
        pub.sendMessage(name.upper())

    def on_menu_symbol(self, item):
        name = Gtk.Buildable.get_name(item)
        pub.sendMessage(name.upper())

    def on_menu_grid_size(self, item):
        name = Gtk.Buildable.get_name(item)
        # get the grid_size option sequence number
        nr = int(name[-1])
        if nr == 1:
            cols, rows = (72, 36)
        elif nr == 2:
            cols, rows = (72, 49)
        elif nr == 3:
            cols, rows = (100, 49)
        elif nr == 4:
            cols, rows = (200, 70)
        else:
            # default, catch all
            cols, rows = (72, 36)
        # strip the sequence nr
        name = name[:-2]
        pub.sendMessage(name.upper(), cols=cols, rows=rows)

    def on_nothing_selected(self):
        self.on_selection_changed()
        self.menu_rotate.set_sensitive(False)
        self.menu_mirror.set_sensitive(False)

    def on_symbol_selected(self, symbol):
        # enable the Symbol menu options only when a symbol has been selected
        self.menu_rotate.set_sensitive(True)
        self.menu_mirror.set_sensitive(True)

    def on_selection_changed(self, selected=False):
        # enable the cut and copy menu only when one or more objects are selected
        self.menu_copy.set_sensitive(selected)
        self.menu_cut.set_sensitive(selected)

    def on_undo_changed(self, undo=False):
        # enable undo only if the undo-stack is not empty
        self.menu_undo.set_sensitive(undo)

    def on_redo_changed(self, redo=False):
        # enable redo only if the redo-stack is not empty
        self.menu_redo.set_sensitive(redo)

    def on_undo(self, button):
        name = Gtk.Buildable.get_name(button)
        pub.sendMessage(name.upper())
