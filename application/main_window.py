"""
AACircuit
2020-03-02 JvO
"""

import os
import sys
from pubsub import pub

from application import INSERT, REMOVE
from application.grid_canvas import GridCanvas
from application.component_canvas import ComponentCanvas

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402
from gi.repository import GdkPixbuf  # noqa: E402

columns = ["Description"]


class MainWindow(Gtk.Window):
    __gtype_name__ = "MainWindow"

    def __new__(cls):
        """
        This method creates and binds the builder window to the class.
        In order for this to work correctly, the class of the main
        window in the Glade UI file must be the same as the name of
        this class.
        """
        app_path = os.path.dirname(__file__)
        try:
            builder = Gtk.Builder()
            builder.add_from_file(os.path.join(app_path, "aacircuit.glade"))
        except IOError:
            print("Failed to load XML GUI file aacircuit.glade")
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
        cssProvider.load_from_path('style.css')
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        # With the others GTK_STYLE_PROVIDER_PRIORITY values get the same result
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.btn_cur = [
            self.builder.get_object("cursor1"),
            self.builder.get_object("cursor2"),
            self.builder.get_object("cursor3"),
            self.builder.get_object("cursor4")]

        self.btn_cur[0].set_active(True)

        # statusbar
        self.label_xpos = self.builder.get_object("x_pos")
        self.label_ypos = self.builder.get_object("y_pos")

        # insert/remove rows or columns
        self.btn_stretch1 = self.builder.get_object("stretch1")
        self.btn_stretch3 = self.builder.get_object("stretch3")
        self.btn_stretch2 = self.builder.get_object("stretch2")
        self.btn_stretch4 = self.builder.get_object("stretch4")

        # clipboard
        self.btn_clipboard = [
            self.builder.get_object("copy_to_clipboard"),
            self.builder.get_object("paste_from_clipboard"),
            self.builder.get_object("load_and_paste_from_clipboard")]

        self.init_grid()
        self.init_cursors()
        self.init_components()

        # connect signals

        self.builder.connect_signals(self)
        self.connect('destroy', lambda w: Gtk.main_quit())

        for btn in self.btn_cur:
            btn.connect("toggled", self.on_toggled_cursor)

        menu_close = self.builder.get_object("quit")
        menu_close.connect("activate", self.on_close_clicked)

        menu_undo = self.builder.get_object("undo")
        menu_undo.connect("activate", self.on_undo)

        self.init_char_buttons()

        # invert/remove rows or columns
        self.btn_stretch1.connect("pressed", self.on_selecting_col)
        self.btn_stretch2.connect("pressed", self.on_selecting_col)
        self.btn_stretch3.connect("pressed", self.on_selecting_row)
        self.btn_stretch4.connect("pressed", self.on_selecting_row)

        # clipboard
        for btn in self.btn_clipboard:
            btn.connect("pressed", self.on_clipboard)

        # subscriptions
        pub.subscribe(self.on_pointer_moved, 'POINTER_MOVED')

    def init_components(self):
        component_canvas = ComponentCanvas(self.builder)  # noqa F841

    def init_grid(self):
        fixed = self.builder.get_object("viewport1")
        self.grid_canvas = GridCanvas()
        fixed.add(self.grid_canvas)

    def init_cursors(self):
        self.cursor = []
        for i in range(1, 5):
            self.cursor.append(GdkPixbuf.Pixbuf.new_from_file("buttons/c{0}.png".format(i)))

    def init_char_buttons(self):
        container = self.builder.get_object("char_table")
        children = container.get_children()
        for btn in children:
            btn.connect("pressed", self.on_char_button_clicked)

    def on_pointer_moved(self, pos):
        # grid indexing starts at zero, show +1
        self.label_xpos.set_text(format(pos[0] + 1))
        self.label_ypos.set_text(format(pos[1] + 1))

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
        pub.sendMessage('COMPONENT_CHANGED', label=char)

    def on_undo(self, button):
        pub.sendMessage('UNDO')

    def on_open_clicked(self, button):
        print("\"Open\" button was clicked")

    def on_close_clicked(self, button):
        print("Closing application")
        Gtk.main_quit()

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

    def custom_cursor(self, btn):
        display = self.get_root_window().get_display()
        pb = self.cursor[btn - 1]
        cursor = Gdk.Cursor.new_from_pixbuf(display, pb, 0, 0)
        # self.get_root_window().set_cursor(cursor)
        widget = self.grid_canvas.drawing_area
        # widget.set_sensitive(False)
        # cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        widget.get_window().set_cursor(cursor)
