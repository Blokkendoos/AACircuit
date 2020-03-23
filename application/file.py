"""
AACircuit.py
2020-03-02 JvO
"""

from pubsub import pub

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk


class FileChooserWindow(Gtk.Window):

    def __init__(self, open=False):

        self.open = open

        if self.open:
            title = "Open file"
        else:
            title = "Save file"

        Gtk.Window.__init__(self, title=title)

        self.on_file_clicked()

    def on_file_clicked(self):

        if self.open:
            option = Gtk.STOCK_OPTION
        else:
            option = Gtk.STOCK_SAVE

        dialog = Gtk.FileChooserDialog("Please choose a file", self,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        option,
                                        Gtk.ResponseType.OK))

        self.add_filters(dialog)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            print("File selected: " + filename)

            if self.open:
                pub.sendMessage('GRID_FROM_FILE', filename=filename)
            else:
                pub.sendMessage('GRID_TO_FILE', filename=filename)

        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name("Text files")
        filter_text.add_mime_type("text/plain")
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name("Any files")
        filter_any.add_pattern("*")
        dialog.add_filter(filter_any)

    def on_folder_clicked(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a folder", self,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                        "Select", Gtk.ResponseType.OK))
        dialog.set_default_size(800, 400)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print("Select clicked")
            print("Folder selected: " + dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print("Cancel clicked")

        dialog.destroy()
