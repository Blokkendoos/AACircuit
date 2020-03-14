"""
AACircuit
2020-03-02 JvO
"""

import os
import sys

from application.grid import Grid
from application.grid_canvas import GridCanvas
from application.component_canvas import ComponentCanvas
from application.component_library import ComponentLibrary

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402
# from gi.repository import GLib  # noqa: E402
from gi.repository import GdkPixbuf  # noqa: E402
from gi.repository import Pango  # noqa: E402

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

        self.btn_cur = [
            self.builder.get_object("btn_cur1"),
            self.builder.get_object("btn_cur2"),
            self.builder.get_object("btn_cur3"),
            self.builder.get_object("btn_cur4")]

        self.btn_cur[0].set_name("btn_cur1")
        self.btn_cur[1].set_name("btn_cur2")
        self.btn_cur[2].set_name("btn_cur3")
        self.btn_cur[3].set_name("btn_cur4")

        self.btn_cur[0].set_active(True)

        self.init_cursors()
        self.grid = Grid(75, 40)
        self.init_grid()
        self.init_components()

        # connect signals

        self.builder.connect_signals(self)
        self.connect('destroy', lambda w: Gtk.main_quit())

        for btn in self.btn_cur:
            btn.connect("toggled", self.on_toggled_cursor)

        btn_close = self.builder.get_object("imagemenuitem5")
        btn_close.connect("activate", self.on_close_clicked)

    def init_components(self):
        component_canvas = ComponentCanvas(self.builder)

    def init_grid(self):
        fixed = self.builder.get_object("viewport1")

        self.grid_canvas = GridCanvas(self.builder)
        self.grid_canvas.grid = self.grid

        fixed.add(self.grid_canvas)

    def init_cursors(self):
        self.cursor = []
        for i in range(1, 5):
            self.cursor.append(GdkPixbuf.Pixbuf.new_from_file("buttons/c{0}.png".format(i)))

    def on_toggled_cursor(self, button):

        if button.get_active():

            name = button.get_name()
            btn = int(name[-1])
            self.custom_cursor(btn)

            # disable the other cursor buttons
            for btn in self.btn_cur:
                if btn.get_name() != button.get_name():
                    # print("Button: %s" % btn.get_name())
                    btn.set_active(False)

    def on_open_clicked(self, button):
        print("\"Open\" button was clicked")

    def on_close_clicked(self, button):
        print("Closing application")
        Gtk.main_quit()

    def custom_cursor(self, btn):
        display = self.get_root_window().get_display()
        pb = self.cursor[btn - 1]
        cursor = Gdk.Cursor.new_from_pixbuf(display, pb, 0, 0)
        # self.get_root_window().set_cursor(cursor)
        widget = self.grid_canvas.drawing_area
        # widget.set_sensitive(False)
        # cursor = Gdk.Cursor(Gdk.CursorType.WATCH)
        widget.get_window().set_cursor(cursor)
