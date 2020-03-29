"""
AACircuit
2020-03-02 JvO
"""

import os
import sys
from pubsub import pub

# from application import _
import locale
from locale import gettext as _

from application import INSERT, REMOVE, IDLE
from application.grid_view import GridView
from application.component_view import ComponentView

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402
from gi.repository import GdkPixbuf  # noqa: E402


class MainWindow(Gtk.Window):
    __gtype_name__ = 'MainWindow'

    def __new__(cls):
        """
        This method creates and binds the builder window to the class.
        In order for this to work correctly, the class of the main
        window in the Glade UI file must be the same as the name of
        this class.
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
            builder.add_from_file(os.path.join(app_path, 'aacircuit.glade'))

        except IOError:
            print(_("Failed to load XML GUI file aacircuit.glade"))
            sys.exit(1)

        new_object = builder.get_object('window1')
        new_object.finish_initializing(builder)

        return new_object

    def finish_initializing(self, builder):
        """
        Treat this as the __init__() method.
        Arguments pass in must be passed from __new__().
        """
        self.builder = builder
        self.set_default_size(640, 480)

        # Add any other initialization here

        # https://stackoverflow.com/questions/14983385/why-css-style-dont-work-on-gtkbutton
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path('application/style.css')
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        # With the others GTK_STYLE_PROVIDER_PRIORITY values get the same result
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # statusbar
        self.label_xpos = self.builder.get_object('x_pos')
        self.label_ypos = self.builder.get_object('y_pos')

        self.builder.connect_signals(self)

        # file menu
        menu_new = self.builder.get_object('new_file')
        menu_open = self.builder.get_object('open_file')
        self.menu_save = self.builder.get_object('save_file')
        self.menu_save_as = self.builder.get_object('save_as_file')

        menu_new.connect('activate', self.on_menu_file)
        menu_open.connect('activate', self.on_menu_file)
        self.menu_save.connect('activate', self.on_menu_file)
        self.menu_save_as.connect('activate', self.on_menu_file)

        self.menu_save.set_sensitive(False)

        self.connect('destroy', lambda w: Gtk.main_quit())
        menu_close = self.builder.get_object('quit')
        menu_close.connect('activate', self.on_close_clicked)

        # edit menu
        menu_copy = self.builder.get_object('copy')
        menu_cut = self.builder.get_object('cut')
        menu_paste = self.builder.get_object('paste')
        menu_delete = self.builder.get_object('delete')
        menu_undo = self.builder.get_object('undo')

        menu_copy.connect('activate', self.on_menu_edit)
        menu_cut.connect('activate', self.on_menu_edit)
        menu_paste.connect('activate', self.on_menu_edit)
        menu_delete.connect('activate', self.on_menu_edit)
        menu_undo.connect('activate', self.on_undo)

        # cursor buttons
        self.btn_cur = [
            self.builder.get_object('cursor1'),
            self.builder.get_object('cursor2'),
            self.builder.get_object('cursor3'),
            self.builder.get_object('cursor4')]

        self.btn_cur[0].set_active(True)

        for btn in self.btn_cur:
            btn.connect('toggled', self.on_toggled_cursor)

        # manipulate symbol
        self.btn_rotate = self.builder.get_object("rotate")
        self.btn_rotate.connect('pressed', self.on_rotate)
        self.btn_rotate.set_tooltip_text(_("rotate the symbol clockwise"))

        self.btn_mirror = self.builder.get_object('mirror')
        self.btn_mirror.connect('pressed', self.on_mirror)
        self.btn_mirror.set_tooltip_text(_("mirror the symbol vertically"))

        # line drawing
        self.btn_mag_line = self.builder.get_object('draw_mag_line')
        self.btn_line0 = self.builder.get_object('draw_line0')
        self.btn_line1 = self.builder.get_object('draw_line1')
        self.btn_line2 = self.builder.get_object('draw_line2')
        self.btn_line3 = self.builder.get_object('draw_line3')
        self.btn_line4 = self.builder.get_object('draw_line4')

        self.btn_mag_line.connect('pressed', self.on_line)
        self.btn_line0.connect('pressed', self.on_line)
        self.btn_line1.connect('pressed', self.on_line)
        self.btn_line2.connect('pressed', self.on_line)
        self.btn_line3.connect('pressed', self.on_line)
        self.btn_line4.connect('pressed', self.on_line)

        self.btn_mag_line.set_tooltip_text(_("MagLine"))
        self.btn_line0.set_tooltip_text(_("free line"))
        self.btn_line1.set_tooltip_text(_("straight line"))
        self.btn_line2.set_tooltip_text(_("line with start and end point 'o'"))
        self.btn_line3.set_tooltip_text(_("line with start and end point '+'"))
        self.btn_line4.set_tooltip_text(_("line with end terminals"))

        self.btn_rect = self.builder.get_object('draw_rect')
        self.btn_rect.connect('pressed', self.on_line)
        self.btn_rect.set_tooltip_text(_("draw a rectangle"))

        # insert/remove rows or columns
        self.btn_stretch1 = self.builder.get_object('stretch1')
        self.btn_stretch3 = self.builder.get_object('stretch3')
        self.btn_stretch2 = self.builder.get_object('stretch2')
        self.btn_stretch4 = self.builder.get_object('stretch4')

        self.btn_stretch1.connect('pressed', self.on_selecting_col)
        self.btn_stretch2.connect('pressed', self.on_selecting_col)
        self.btn_stretch3.connect('pressed', self.on_selecting_row)
        self.btn_stretch4.connect('pressed', self.on_selecting_row)

        self.btn_stretch1.set_tooltip_text(_("insert rows"))
        self.btn_stretch3.set_tooltip_text(_("insert columns"))
        self.btn_stretch2.set_tooltip_text(_("remove rows"))
        self.btn_stretch4.set_tooltip_text(_("remove columns"))

        self.btn_select = self.builder.get_object("select_rect")
        self.btn_select.connect('pressed', self.on_select_rect)

        # clipboard
        self.btn_clipboard = [
            self.builder.get_object('copy_to_clipboard'),
            self.builder.get_object('paste_from_clipboard'),
            self.builder.get_object('load_and_paste_from_clipboard')]
        for btn in self.btn_clipboard:
            btn.connect('pressed', self.on_clipboard)

        self.btn_clipboard[0].set_tooltip_text(_("copy grid to clipboard"))
        self.btn_clipboard[1].set_tooltip_text(_("paste grid from clipboard"))
        self.btn_clipboard[2].set_tooltip_text(_("load file and paste into grid"))

        self.init_grid()
        self.init_cursors()
        self.init_components()
        self.init_char_buttons()

        # subscriptions

        pub.subscribe(self.on_pointer_moved, 'POINTER_MOVED')
        pub.subscribe(self.on_file_opened, 'FILE_OPENED')

    def init_components(self):
        component_canvas = ComponentView(self.builder)  # noqa F841

    def init_grid(self):
        fixed = self.builder.get_object('grid_viewport')
        self.grid_view = GridView()
        fixed.add(self.grid_view)

    def init_cursors(self):
        self.cursor = []
        for i in range(1, 5):
            self.cursor.append(GdkPixbuf.Pixbuf.new_from_file("application/buttons/c{0}.png".format(i)))

    def init_char_buttons(self):
        container = self.builder.get_object('char_table')
        children = container.get_children()
        for btn in children:
            btn.connect('pressed', self.on_char_button_clicked)

    def on_pointer_moved(self, pos):
        """Update the pointer position in the statusbar"""
        # grid indexing starts at zero, show +1
        self.label_xpos.set_text(format(pos.x + 1))
        self.label_ypos.set_text(format(pos.y + 1))

    def on_rotate(self, button):
        pub.sendMessage('ROTATE_SYMBOL')

    def on_mirror(self, button):
        pub.sendMessage('MIRROR_SYMBOL')

    def on_line(self, button):
        name = Gtk.Buildable.get_name(button)
        type = name[-1]
        pub.sendMessage(name.upper(), type=type)

    def on_toggled_cursor(self, button):

        if button.get_active():

            name = Gtk.Buildable.get_name(button)
            btn = int(name[-1])
            self.custom_cursor(btn)

            # disable the other cursor buttons
            for btn in self.btn_cur:
                if Gtk.Buildable.get_name(btn) != Gtk.Buildable.get_name(button):
                    # print("Button: %s" % btn.get_name())
                    btn.set_active(False)

    def on_char_button_clicked(self, button):
        char = button.get_label()
        pub.sendMessage('CHARACTER_CHANGED', label=char)

    def on_undo(self, button):
        pub.sendMessage('UNDO')

    def on_close_clicked(self, button):
        print(_("Closing application"))
        Gtk.main_quit()

    def on_select_rect(self, button):
        pub.sendMessage('SELECT_RECT', action=IDLE)

    def on_selecting_col(self, button):
        # https://stackoverflow.com/questions/3489520/python-gtk-widget-name
        name = Gtk.Buildable.get_name(button)
        if name == 'stretch1':
            action = INSERT
        else:
            action = REMOVE
        pub.sendMessage('SELECTING_COL', action=action)

    def on_selecting_row(self, button):
        name = Gtk.Buildable.get_name(button)
        if name == 'stretch3':
            action = INSERT
        else:
            action = REMOVE
        pub.sendMessage('SELECTING_ROW', action=action)

    def on_clipboard(self, button):
        name = Gtk.Buildable.get_name(button)
        pub.sendMessage(name.upper())

    def on_menu_file(self, item):
        name = Gtk.Buildable.get_name(item).upper()
        pub.sendMessage(name)

    def on_file_opened(self):
        # only when a file is opened, enable 'save' in the File menu
        self.menu_save.set_sensitive(True)

    def on_menu_edit(self, item):
        # menu cut|copy|paste
        name = Gtk.Buildable.get_name(item)
        pos, width, height = self.grid_view.drag_rect
        pub.sendMessage(name.upper(), pos=pos, rect=(width, height))

    def custom_cursor(self, btn):
        display = self.get_root_window().get_display()

        pb = self.cursor[btn - 1]
        # the cursor hot-spot is at the center of the (16x16) cursor image
        cursor = Gdk.Cursor.new_from_pixbuf(display, pb, 8, 15)

        widget = self.grid_view._drawing_area
        widget.get_window().set_cursor(cursor)
