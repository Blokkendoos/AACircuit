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
            self.filename = dialog.get_filename()
            self.action()

        dialog.destroy()

    def action(self):
        # print(_("File selected: %s") % self.filename)
        if self.open:
            pub.sendMessage('READ_FROM_FILE', filename=self.filename)
        else:
            pub.sendMessage('WRITE_TO_FILE', filename=self.filename)

    def add_filters(self, dialog):
        filter_aac = Gtk.FileFilter()
        filter_aac.set_name(_("AAC files"))
        filter_aac.add_pattern('*.aac')
        dialog.add_filter(filter_aac)

        filter_text = Gtk.FileFilter()
        filter_text.set_name(_("Text files"))
        filter_text.add_mime_type('text/plain')
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("All files"))
        filter_any.add_pattern('*')
        dialog.add_filter(filter_any)

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
            msg = _("Folder selected: %s") % dialog.get_filename()
            pub.sendMessage('STATUS_MESSAGE', msg=msg)

        dialog.destroy()


class AsciiFileChooserWindow(FileChooserWindow):

    def __init__(self):
        super(AsciiFileChooserWindow, self).__init__(open=True)

    def action(self):
        pub.sendMessage('LOAD_ASCII_FROM_FILE', filename=self.filename)

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name(_("Text files"))
        filter_text.add_mime_type('text/plain')
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("All files"))
        filter_any.add_pattern('*')
        dialog.add_filter(filter_any)


class PrintOperation(object):

    settings = Gtk.PrintSettings()

    def __init__(self, parent):

        # https://askubuntu.com/questions/220350/how-to-add-a-print-dialog-to-an-application
        # https://stackoverflow.com/questions/28325525/python-gtk-printoperation-print-a-pdf

        self.parent = parent
        self.printop = Gtk.PrintOperation()

        self.printop.set_embed_page_setup(True)
        self.printop.set_print_settings(self.settings)

        self.printop.connect('begin-print', self.on_begin_print)
        self.printop.connect('draw-page', self.on_draw_page)
        # self.printop.connect('end-print', self.on_end_print)

    def run(self):

        result = self.printop.run(Gtk.PrintOperationAction.PRINT_DIALOG,
                                  self.parent)

        if result == Gtk.PrintOperationResult.ERROR:
            print(self.printop.get_error())

        elif result == Gtk.PrintOperationResult.APPLY:
            self.settings = self.printop.get_print_settings()

    def on_begin_print(self, operation, print_ctx):
        parms = (operation, print_ctx)
        pub.sendMessage('BEGIN_PRINT', parms=parms)

    def on_draw_page(self, operation, print_ctx, page_num):
        parms = (operation, print_ctx, page_num)
        pub.sendMessage('DRAW_PAGE', parms=parms)
