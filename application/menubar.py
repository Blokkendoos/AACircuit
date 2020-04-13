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

        menu_new.connect('activate', self.on_menu_file)
        menu_open.connect('activate', self.on_menu_file)
        self.menu_save.connect('activate', self.on_menu_file)
        self.menu_save_as.connect('activate', self.on_menu_file)

        self.menu_save.set_sensitive(False)

        # edit menu
        self.menu_copy = builder.get_object('copy')
        self.menu_cut = builder.get_object('cut')
        self.menu_paste = builder.get_object('paste')
        self.menu_undo = builder.get_object('undo')

        self.menu_copy.connect('activate', self.on_menu_edit)
        self.menu_cut.connect('activate', self.on_menu_edit)
        self.menu_paste.connect('activate', self.on_menu_edit)
        self.menu_undo.connect('activate', self.on_undo)

        self.menu_copy.set_sensitive(False)
        self.menu_cut.set_sensitive(False)
        self.menu_paste.set_sensitive(False)
        self.menu_undo.set_sensitive(False)

        pub.subscribe(self.on_file_opened, 'FILE_OPENED')
        pub.subscribe(self.on_nothing_selected, 'NOTHING_SELECTED')
        pub.subscribe(self.on_selection_changed, 'SELECTION_CHANGED')
        pub.subscribe(self.on_undo_changed, 'UNDO_CHANGED')

    def on_menu_file(self, item):
        name = Gtk.Buildable.get_name(item).upper()
        pub.sendMessage(name)

    def on_file_opened(self):
        # only when a file is opened, enable 'save' in the File menu
        self.menu_save.set_sensitive(True)

    def on_menu_edit(self, item):
        # menu cut|copy|paste
        name = Gtk.Buildable.get_name(item)

        # get the rectangle (ul and br have been set in drag begin/end)
        ul, br = self.grid_view.drag_rect

        pub.sendMessage(name.upper(), rect=(ul, br))

    def on_nothing_selected(self):
        self.on_selection_changed()

    def on_selection_changed(self, selected=False):
        # enable the cut and copy menu only when one or more objects are selected
        self.menu_copy.set_sensitive(selected)
        self.menu_cut.set_sensitive(selected)

    def on_undo_changed(self, undo=False):
        # enable undo only if the undo-stack is not empty
        self.menu_undo.set_sensitive(undo)

    def on_undo(self, button):
        pub.sendMessage('UNDO')
