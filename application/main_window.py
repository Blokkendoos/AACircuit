"""
AACircuit
2020-03-02 JvO
"""

import os
import sys

from application.component_library import ComponentLibrary
from application.grid import Grid
from application.grid_canvas import GridCanvas

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402
from gi.repository import GLib  # noqa: E402


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
        self.set_default_size(640, 480)

        # Add any other initialization here

        self.btn_cur = [
            builder.get_object("btn_cur1"),
            builder.get_object("btn_cur2"),
            builder.get_object("btn_cur3"),
            builder.get_object("btn_cur4")]

        self.btn_cur[0].set_name("btn_cur1")
        self.btn_cur[1].set_name("btn_cur2")
        self.btn_cur[2].set_name("btn_cur3")
        self.btn_cur[3].set_name("btn_cur4")

        self.btn_cur[0].set_active(True)

        # connect signals

        builder.connect_signals(self)
        self.connect('destroy', lambda w: Gtk.main_quit())

        for btn in self.btn_cur:
            btn.connect("toggled", self._on_toggled_cursor)

        btn_close = builder.get_object("imagemenuitem5")
        btn_close.connect("activate", self._on_close_clicked)

        # component libraries

        self.lib = ComponentLibrary()
        print("Number of component libraries loaded: {0}".format(self.lib.nr_libraries()))

        # the ASCII grid

        self.grid = Grid(75, 40)

        fixed = builder.get_object("viewport1")

        grid_canvas = GridCanvas()
        grid_canvas.grid = self.grid
        self._grid_canvas = grid_canvas

        fixed.add(grid_canvas)

    def _on_toggled_cursor(self, button, data=None):

        if button.get_active():

            # https://askubuntu.com/questions/138336/how-to-change-the-cursor-to-hourglass-in-a-python-gtk3-application
            # cursor = Gdk.Cursor.new(Gdk.CursorType.WATCH)

            name = button.get_name()

            # https://developer.gnome.org/gdk3/stable/gdk3-Cursors.html#gdk-cursor-new-from-name
            if name == "btn_cur1":
                cursor = Gdk.Cursor.new(Gdk.CursorType.LEFT_PTR)
            elif name == "btn_cur2":
                cursor = Gdk.Cursor.new(Gdk.CursorType.CROSSHAIR)
            elif name == "btn_cur3":
                cursor = Gdk.Cursor.new(Gdk.CursorType.WATCH)
            elif name == "btn_cur4":
                cursor = Gdk.Cursor.new(Gdk.CursorType.CROSSHAIR)
            self.get_root_window().set_cursor(cursor)

            # disable the other cursor buttons
            for btn in self.btn_cur:
                if btn.get_name() != button.get_name():
                    # print("Button: %s" % btn.get_name())
                    btn.set_active(False)

    def _on_open_clicked(self, button):
        print("\"Open\" button was clicked")

    def _on_close_clicked(self, button):
        print("Closing application")
        Gtk.main_quit()
