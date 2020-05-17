"""
AACircuit
2020-03-02 JvO
"""

import sys
import locale
from locale import gettext as _
from pubsub import pub
from application import get_path_to_data

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

        try:
            # https://askubuntu.com/questions/140552/how-to-make-glade-load-translations-from-opt
            # For this particular case the locale module needs to be used instead of gettext.
            # Python's gettext module is pure python, it doesn't actually set the text domain
            # in a way that the C library can read, but locale does (by calling libc).
            locale.bindtextdomain('aacircuit', get_path_to_data('locale/'))
            locale.textdomain('aacircuit')

            builder = Gtk.Builder()
            # https://stackoverflow.com/questions/24320502/how-to-translate-pygtk-glade-gtk-builder-application
            builder.set_translation_domain('aacircuit')
            builder.add_from_file(get_path_to_data('memo_editing_dialog.glade'))

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
        css_provider.load_from_path(get_path_to_data('style.css'))

        style_context = self.get_style_context()
        style_context.add_provider(css_provider,
                                   Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self._text = memo
        self._memo_editable = False

        self.init_scrolled_window(builder)
        self.enable_memo_text()

        self.show_all()

    def init_scrolled_window(self, builder):

        # FIXME the scrollbars (hadjustment) get set correctly only after having scrolled to the end of the text (in the textview)
        self.memo_tv = builder.get_object('memo_textview')

        self.text_buffer = self.memo_tv.get_buffer()
        self.text_buffer.set_text(self._text)

        tt = self.text_buffer.get_tag_table()

        self.tag_editable = Gtk.TextTag()
        self.tag_editable.set_property('foreground', '#000000')
        tt.add(self.tag_editable)

        # locked text is shown in light gray
        self.tag_locked = Gtk.TextTag()
        self.tag_locked.set_property('foreground', '#7f7f7f')
        tt.add(self.tag_locked)

        self.tag_match = Gtk.TextTag()
        self.tag_match.set_property('background', 'yellow')
        tt.add(self.tag_match)

    def enable_memo_text(self):
        editable = self._memo_editable
        self.memo_tv.set_editable(editable)
        self.memo_tv.set_cursor_visible(editable)

        bounds = self.text_buffer.get_bounds()
        if bounds:
            start, end = bounds
            self.text_buffer.remove_all_tags(start, end)
            if editable:
                self.text_buffer.apply_tag(self.tag_editable, start, end)
            else:
                self.text_buffer.apply_tag(self.tag_locked, start, end)

    def on_edit_memo(self, item, data):
        self._memo_editable = item.get_active()
        self.enable_memo_text()

    def on_draw_clicked(self, item):
        start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        text = self.text_buffer.get_text(start, end, False)
        pub.sendMessage('RERUN_MEMO', str=text)

    def on_search_changed(self, widget):
        self.search_and_mark(widget.get_text())

    def search_and_mark(self, text):
        start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        self.text_buffer.remove_tag(self.tag_match, start, end)

        match = start.forward_search(text, Gtk.TextSearchFlags.TEXT_ONLY, end)

        if match is not None:
            # scroll to the first hit
            match_start, match_end = match
            self.memo_tv.scroll_to_iter(match_start, 0.0, True, 0, 0)

        while match is not None:
            match_start, match_end = match
            self.text_buffer.apply_tag(self.tag_match, match_start, match_end)
            start = match_end
            match = start.forward_search(text, Gtk.TextSearchFlags.TEXT_ONLY, end)

    def on_next_match(self, item):
        print("Not yet implemented")

    def on_previous_match(self, item):
        print("Not yet implemented")

    def on_stop_search(self, item):
        start = self.text_buffer.get_start_iter()
        end = self.text_buffer.get_end_iter()
        self.text_buffer.remove_tag(self.tag_match, start, end)
