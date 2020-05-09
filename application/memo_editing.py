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

        self._text = memo
        self._memo_editable = False

        self.init_scrolled_window(builder)
        self.init_text()
        self.enable_memo_text()

        self.show_all()

    def init_scrolled_window(self, builder):

        def setup_sub_scrolled_window(textview):
            # https://stackoverflow.com/questions/6617816/two-gtk-textview-widgets-with-shared-scrollbar
            sw = Gtk.ScrolledWindow()

            # don't show the scrollbars on these sub-scrolledwindows
            sw.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.NEVER)
            sw.add(textview)

            textview.set_monospace(True)
            textview.set_editable(False)
            textview.set_cursor_visible(False)

            return sw

        box = Gtk.HBox()
        textview1 = Gtk.TextView()
        textview2 = Gtk.TextView()

        # FIXME set_size_request() makes the view content to be updated only after being selected
        # textview1.set_size_request(25, -1)
        textview1.set_justification(Gtk.Justification.RIGHT)
        # textview1.set_css_name('linenr')
        textview1.set_name('linenr')  # use this name in CSS selector (!)

        sw1 = setup_sub_scrolled_window(textview1)
        sw2 = setup_sub_scrolled_window(textview2)

        # use the first scrolledwindow's adjustments
        sw2.set_hadjustment(sw1.get_hadjustment())
        sw2.set_vadjustment(sw1.get_vadjustment())

        box.pack_start(sw1, False, False, padding=5)
        box.pack_start(sw2, True, True, padding=5)

        # main scrolled window
        main_sw = builder.get_object('main_sw')
        main_sw.add(box)

        self.memo_tv = textview2
        self.text_buffer = textview2.get_buffer()

        self.linenr_tv = textview1
        self.linenr_buffer = textview1.get_buffer()

        tt = self.text_buffer.get_tag_table()
        self.editable_tag = Gtk.TextTag()
        self.editable_tag.set_property('foreground', '#000000')
        tt.add(self.editable_tag)

        # locked text is shown in light gray
        self.locked_tag = Gtk.TextTag()
        self.locked_tag.set_property('foreground', '#7f7f7f')
        tt.add(self.locked_tag)

    def init_text(self):
        self.text_buffer.set_text(self._text)
        # linenumbers
        lines = self._text.splitlines()
        str = ""
        for i in range(1, len(lines) + 1):
            str += "{}\n".format(i)
        self.linenr_buffer.set_text(str)

    def enable_memo_text(self):
        editable = self._memo_editable
        self.memo_tv.set_editable(editable)
        self.memo_tv.set_cursor_visible(editable)

        bounds = self.text_buffer.get_bounds()
        start, end = bounds
        if bounds:
            self.text_buffer.remove_all_tags(start, end)
            if editable:
                self.text_buffer.apply_tag(self.editable_tag, start, end)
            else:
                self.text_buffer.apply_tag(self.locked_tag, start, end)

    def on_edit_memo(self, item, data):
        self._memo_editable = item.get_active()
        self.enable_memo_text()

    def on_draw_clicked(self, item):
        start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        text = self.text_buffer.get_text(start, end, False)
        pub.sendMessage('RERUN_MEMO', str=text)
