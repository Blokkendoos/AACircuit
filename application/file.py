"""
AACircuit.py
2020-03-02 JvO
"""

from pubsub import pub
from application import _

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402


class InputFileChooser():

    def __init__(self):
        dialog = Gtk.FileChooserDialog(title=_("Please choose a file"),
                                       action=Gtk.FileChooserAction.SAVE,
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                                Gtk.STOCK_OPEN, Gtk.ResponseType.OK))

        dialog.set_default_size(640, 480)
        self.add_filters(dialog)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.filename = dialog.get_filename()
            self.action()
        dialog.destroy()

    def action(self):
        pub.sendMessage('READ_FROM_FILE', filename=self.filename)

    def add_filters(self, dialog):
        filter_aac = Gtk.FileFilter()
        filter_aac.set_name(_("Circuit files"))
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


class OutputFileChooser():

    def __init__(self, filename=_("Untitled_schema.aac")):
        self.filename = filename
        dialog = Gtk.FileChooserDialog(title=_("Save as"),
                                       action=Gtk.FileChooserAction.SAVE,
                                       buttons=(Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                                                Gtk.STOCK_SAVE, Gtk.ResponseType.OK))

        dialog.set_default_size(640, 480)
        dialog.props.do_overwrite_confirmation = True
        dialog.set_current_name(self.filename)
        self.add_filters(dialog)
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.filename = dialog.get_filename()
            self.action()
        dialog.destroy()

    def action(self):
        pub.sendMessage('WRITE_TO_FILE', filename=self.filename)

    def add_filters(self, dialog):
        filter_aac = Gtk.FileFilter()
        filter_aac.set_name(_("Circuit files"))
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


class OutputFilePDF(OutputFileChooser):

    def __init__(self, filename):
        # filename is set in the Gtk PDF writer
        super(OutputFilePDF, self).__init__(filename)

    def action(self):
        pub.sendMessage('DRAW_PDF', filename=self.filename)

    def add_filters(self, dialog):
        filter_aac = Gtk.FileFilter()
        filter_aac.set_name(_("PDF files"))
        filter_aac.add_pattern('*.pdf')
        dialog.add_filter(filter_aac)


class OutputFileAscii(OutputFileChooser):

    def __init__(self):
        super(OutputFileAscii, self).__init__(filename=_("Untitled_schema.txt"))

    def action(self):
        pub.sendMessage('WRITE_TO_ASCII_FILE', filename=self.filename)

    def add_filters(self, dialog):
        filter_text = Gtk.FileFilter()
        filter_text.set_name(_("Text files"))
        filter_text.add_mime_type('text/plain')
        dialog.add_filter(filter_text)

        filter_any = Gtk.FileFilter()
        filter_any.set_name(_("All files"))
        filter_any.add_pattern('*')
        dialog.add_filter(filter_any)


class InputFileAscii(InputFileChooser):

    def __init__(self):
        super(InputFileAscii, self).__init__()

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

    def __init__(self):

        # https://askubuntu.com/questions/220350/how-to-add-a-print-dialog-to-an-application
        # https://stackoverflow.com/questions/28325525/python-gtk-printoperation-print-a-pdf

        self.printop = Gtk.PrintOperation()

        # w/o async closing the app stalls
        self.printop.set_allow_async(False)
        self.printop.set_n_pages(1)  # TODO set nr pages

        self.printop.set_embed_page_setup(True)
        self.printop.set_print_settings(self.settings)

        # self.printop.connect('begin-print', self.on_begin_print)
        self.printop.connect('draw-page', self.on_draw_page)
        self.printop.connect('end-print', self.on_end_print)

    def run(self, parent=None):
        result = self.printop.run(Gtk.PrintOperationAction.PRINT_DIALOG,
                                  parent)
        if result == Gtk.PrintOperationResult.ERROR:
            print(self.printop.get_error())
        elif result == Gtk.PrintOperationResult.APPLY:
            self.settings = self.printop.get_print_settings()

    def on_begin_print(self, operation, print_ctx):
        pub.sendMessage('BEGIN_PRINT')

    def on_draw_page(self, operation, print_ctx, page_num):
        parms = (operation, print_ctx, page_num)
        pub.sendMessage('DRAW_PAGE', parms=parms)

    def on_end_print(self, operation, print_ctx):
        pub.sendMessage('END_PRINT')
