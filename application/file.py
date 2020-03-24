"""
AACircuit.py
2020-03-02 JvO
"""

from pubsub import pub
from application import _

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402


class FileChooserWindow(Gtk.Window):

    def __init__(self, open=False):

        self.open = open

        if self.open:
            title = _("Open file")
        else:
            title = _("Save file")

        Gtk.Window.__init__(self, title=title)

        self.on_file_clicked()

    def on_file_clicked(self):

        if self.open:
            option = Gtk.STOCK_OPEN
        else:
            option = Gtk.STOCK_SAVE

        dialog = Gtk.FileChooserDialog(_("Please choose a file"), self,
                                       Gtk.FileChooserAction.SAVE,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        option,
                                        Gtk.ResponseType.OK))
        dialog.set_default_size(640, 480)

        self.add_filters(dialog)

        response = dialog.run()

        if response == Gtk.ResponseType.OK:
            filename = dialog.get_filename()
            print(_("File selected: %s") % filename)

            if self.open:
                pub.sendMessage('READ_FROM_FILE', filename=filename)
            else:
                pub.sendMessage('WRITE_TO_FILE', filename=filename)

        elif response == Gtk.ResponseType.CANCEL:
            print(_("Cancel clicked"))

        dialog.destroy()

    def add_filters(self, dialog):
        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("Any files"))
        filter_any.add_pattern('*')
        dialog.add_filter(filter_any)

        filter_text = Gtk.FileFilter()
        filter_text.set_name(_("Text files"))
        filter_text.add_mime_type('text/plain')
        dialog.add_filter(filter_text)

    def on_folder_clicked(self, widget):
        dialog = Gtk.FileChooserDialog(_("Please choose a folder"), self,
                                       Gtk.FileChooserAction.SELECT_FOLDER,
                                       (Gtk.STOCK_CANCEL,
                                        Gtk.ResponseType.CANCEL,
                                        _("Select"),
                                        Gtk.ResponseType.OK))
        dialog.set_default_size(640, 480)

        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            print(_("Folder selected: %s") % dialog.get_filename())
        elif response == Gtk.ResponseType.CANCEL:
            print(_("Cancel clicked"))

        dialog.destroy()
