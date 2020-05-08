"""
AACircuit
2020-03-02 JvO
"""

import os
import sys
import locale
from locale import gettext as _
from pubsub import pub

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk  # noqa: E402


class MemoEditingDialog(Gtk.Dialog):
    __gtype_name__ = 'MemoEditingDialog'

    def __new__(cls, memo):
        """
        This method creates and binds the builder window to the class.
        In order for this to work correctly, the class of the main
        window in the Glade UI file must be the same as the name of
        this class.

        https://eeperry.wordpress.com/2013/01/05/pygtk-new-style-python-class-using-builder/
        """
        app_path = os.path.dirname(__file__)

        try:
            # https://askubuntu.com/questions/140552/how-to-make-glade-load-translations-from-opt
            # For this particular case the locale module needs to be used instead of gettext.
            # Python's gettext module is pure python, it doesn't actually set the text domain
            # in a way that the C library can read, but locale does (by calling libc).
            locale.bindtextdomain('aacircuit', 'locale/')
            locale.textdomain('aacircuit')

            builder = Gtk.Builder()
            # https://stackoverflow.com/questions/24320502/how-to-translate-pygtk-glade-gtk-builder-application
            builder.set_translation_domain('aacircuit')
            builder.add_from_file(os.path.join(app_path, 'memo_editing_dialog.glade'))

        except IOError:
            print(_("Failed to load XML GUI file memo_editing_dialog.glade"))
            sys.exit(1)

        new_object = builder.get_object('memo_editing')
        new_object.finish_initializing(builder, memo)

        return new_object

    def finish_initializing(self, builder, memo):
        """
        Treat this as the __init__() method.
        Arguments pass in must be passed from __new__().
        """
        builder.connect_signals(self)

        # Add any other initialization here

        css_provider = Gtk.CssProvider()
        css_provider.load_from_path('application/style.css')

        style_context = self.get_style_context()
        style_context.add_provider(css_provider,
                                   Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._memo_editable = False

        self.text_buffer = Gtk.TextBuffer()
        self.text_buffer.set_text(memo)

        self.memo_text = builder.get_object('memo_text')
        self.memo_text.set_buffer(self.text_buffer)
        self.memo_text.set_monospace(True)

        tt = self.text_buffer.get_tag_table()
        self.editable_tag = Gtk.TextTag()
        self.editable_tag.set_property('foreground', '#000000')
        tt.add(self.editable_tag)

        # locked text is shown in light gray
        self.locked_tag = Gtk.TextTag()
        self.locked_tag.set_property('foreground', '#7f7f7f')
        tt.add(self.locked_tag)

        self.enable_memo_text()

        self.show_all()

    def enable_memo_text(self):
        editable = self._memo_editable

        self.memo_text.set_editable(editable)
        self.memo_text.set_cursor_visible(editable)

        # start = self.text_buffer.get_start_iter()
        # end = self.text_buffer.get_end_iter()
        bounds = self.text_buffer.get_bounds()
        start, end = bounds
        if bounds:
            if editable:
                self.text_buffer.remove_all_tags(start, end)
                self.text_buffer.apply_tag(self.editable_tag, start, end)
            else:
                self.text_buffer.remove_all_tags(start, end)
                self.text_buffer.apply_tag(self.locked_tag, start, end)

    def on_edit_memo(self, item, data):
        self._memo_editable = item.get_active()
        self.enable_memo_text()

    def on_draw_clicked(self, item):
        start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        text = self.text_buffer.get_text(start, end, False)
        pub.sendMessage('RERUN_MEMO', str=text)
