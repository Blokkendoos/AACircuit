"""
AACircuit
2020-03-02 JvO
"""

import cairo

from application.pos import Pos
from application.symbol import MagLine
from application.preferences import Preferences, SingleCharEntry

import os
import sys
import locale
from locale import gettext as _

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402

gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo  # noqa: E402


class MagicLineSettingsDialog(Gtk.Dialog):
    __gtype_name__ = 'MagicLineSettingsDialog'

    def __new__(cls):
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
            builder.add_from_file(os.path.join(app_path, 'magic_line_dialog.glade'))

        except IOError:
            print(_("Failed to load XML GUI file preferences_dialog.glade"))
            sys.exit(1)

        new_object = builder.get_object('magic_line_settings')
        new_object.finish_initializing(builder)

        return new_object

    def finish_initializing(self, builder):
        """
        Treat this as the __init__() method.
        Arguments pass in must be passed from __new__().
        """
        builder.connect_signals(self)
        self.set_default_size(500, 225)

        # Add any other initialization here

        # https://stackoverflow.com/questions/14983385/why-css-style-dont-work-on-gtkbutton
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path('application/style.css')
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        # With the others GTK_STYLE_PROVIDER_PRIORITY values get the same result
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.line_matching_data = MagLine.LMD
        self.init_matrix(builder)

        self.show_all()

    def init_matrix(self, builder):
        frame = builder.get_object('matrix_viewport')

    def on_previous_matrix(self, item):
        print("Not yet implemented")

    def on_next_matrix(self, item):
        print("Not yet implemented")

    def on_start_direction_changed(self, item):
        print("Not yet implemented")

    def on_start_character_changed(self, item):
        print("Not yet implemented")

    def on_create_new_matrix(self, item):
        print("Not yet implemented")

    def on_refresh(self, item):
        print("Not yet implemented")

    def on_save_clicked(self, item):
        print("Not yet implemented")


class MatrixView(Gtk.Frame):

    def __init__(self):

        super(MatrixView, self).__init__()

        self.set_border_width(0)

        self.surface = None
        self._grid = None
        self._hover_pos = Pos(0, 0)

        # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html
        self._drawing_area = Gtk.DrawingArea()
        self.add(self._drawing_area)

        self._drawing_area.set_can_focus(True)

        self._drawing_area.connect('draw', self.on_draw)
        self._drawing_area.connect('configure-event', self.on_configure)

        # https://www.programcreek.com/python/example/84675/gi.repository.Gtk.DrawingArea
        self._drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self._drawing_area.connect('button-press-event', self.on_button_press)

        # https://stackoverflow.com/questions/44098084/how-do-i-handle-keyboard-events-in-gtk3
        self._drawing_area.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self._drawing_area.connect('key-press-event', self.on_key_press)

        self._drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self._drawing_area.connect('motion-notify-event', self.on_hover)

    def init_surface(self, area):
        """Initialize Cairo surface."""
        if self.surface is not None:
            # destroy previous buffer
            self.surface.finish()
            self.surface = None

        # create a new buffer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())

    @property
    def max_pos_grid(self):
        # the decision matrix dimensions are 3x3
        x_max = 3 * Preferences.values['GRIDSIZE_W']
        y_max = 3 * Preferences.values['GRIDSIZE_H']
        return Pos(x_max, y_max)

    def on_configure(self, area, event, data=None):
        self.init_surface(self._drawing_area)
        context = cairo.Context(self.surface)
        self.do_drawing(context)
        self.surface.flush()
        return False

    def on_draw(self, area, ctx):
        if self.surface is not None:
            ctx.set_source_surface(self.surface, 0.0, 0.0)
            ctx.paint()
        else:
            print(_("Invalid surface"))
        return False

    def do_drawing(self, ctx):
        self.draw_background(ctx)
        self.draw_gridlines(ctx)
        self.draw_content(ctx)
        self.draw_selection(ctx)
        self.queue_draw()

    def draw_background(self, ctx):
        """Draw a background with the size of the grid."""

        ctx.set_source_rgb(0.95, 0.95, 0.85)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max, y_max = self.max_pos_grid.xy

        ctx.new_path()
        ctx.rectangle(0, 0, x_max, y_max)
        ctx.fill()

    def draw_gridlines(self, ctx):

        # TODO use CSS for uniform colors?
        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max, y_max = self.max_pos.xy
        x_incr = Preferences.values['GRIDSIZE_W']
        y_incr = Preferences.values['GRIDSIZE_H']

        # horizontal lines
        y = Preferences.values['GRIDSIZE_H']
        while y <= y_max:
            ctx.new_path()
            ctx.move_to(0, y)
            ctx.line_to(x_max, y)
            ctx.stroke()
            y += y_incr

        # vertical lines
        x = 0
        while x <= x_max:
            ctx.new_path()
            ctx.move_to(x, 0)
            ctx.line_to(x, y_max)
            ctx.stroke()
            x += x_incr

    def draw_content(self, ctx):

        if self._grid is None:
            return

        ctx.set_source_rgb(0.1, 0.1, 0.1)

        use_pango_font = Preferences.values['PANGO_FONT']

        if use_pango_font:
            # https://sites.google.com/site/randomcodecollections/home/python-gtk-3-pango-cairo-example
            # https://developer.gnome.org/pango/stable/pango-Cairo-Rendering.html
            layout = PangoCairo.create_layout(ctx)
            desc = Pango.font_description_from_string(Preferences.values['FONT'])
            layout.set_font_description(desc)
        else:
            ctx.set_font_size(Preferences.values['FONTSIZE'])
            ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        y = 0
        for r in self._grid.grid:

            x = 0
            for c in r:

                if use_pango_font:
                    ctx.move_to(x, y)
                    layout.set_text(str(c), -1)
                    PangoCairo.show_layout(ctx, layout)
                else:
                    # the Cairo text glyph origin is its left-bottom corner
                    ctx.move_to(x, y + Preferences.values['FONTSIZE'])
                    ctx.show_text(str(c))

                x += Preferences.values['GRIDSIZE_W']

            y += Preferences.values['GRIDSIZE_H']
