"""
AACircuit
2020-03-02 JvO
"""

import cairo
import time
from pubsub import pub

from application.pos import Pos
from application.symbol import MagLine
from application.preferences import Preferences, SingleCharEntry

import os
import sys
import locale
from locale import gettext as _

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

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

        self.line_matching_data = MagLine.LMD
        self.matrix_nr = 1

        self.init_matrix_view(builder)
        self.init_start_orientation(builder)
        self.init_start_character(builder)
        self.update_line_matching_data()

        self.show_all()

    def init_start_orientation(self, builder):

        # TODO use literals
        ori_store = Gtk.ListStore(int, str)
        ori_store.append([0, _("Horizontal")])
        ori_store.append([1, _("Vertical")])
        ori_store.append([2, _("Longest first")])

        # https://python-gtk-3-tutorial.readthedocs.io/en/latest/combobox.html
        combobox = builder.get_object('start_direction')

        # https://stackoverflow.com/questions/9983469/gtk3-combobox-shows-parent-items-from-a-treestore
        cell = Gtk.CellRendererText()
        combobox.pack_start(cell, True)
        combobox.add_attribute(cell, 'text', 1)
        combobox.set_model(ori_store)
        self._start_ori_combo = combobox

    def init_start_character(self, builder):
        start_box = builder.get_object('start_box')
        start_character = SingleCharEntry()
        start_box.add(start_character)
        # self._start_character = builder.get_object('start_character')
        self._start_character = start_character

    def update_line_matching_data(self):
        lmd = self.line_matching_data[self.matrix_nr]
        self._start_character.set_text(lmd.char)

        lmd = self.line_matching_data[self.matrix_nr]
        self._start_ori_combo.set_active(lmd.ori)

    def init_matrix_view(self, builder):
        frame = builder.get_object('matrix_frame')
        # frame.set_shadow_type(Gtk.ShadowType.IN)

        view = builder.get_object('matrix_viewport')
        self.matrix_view = MatrixView(self.line_matching_data[self.matrix_nr])

        view.add(self.matrix_view)

    def on_previous_matrix(self, item):
        self.matrix_nr += 1
        self.matrix_nr %= len(self.line_matching_data)

        self.update_line_matching_data()
        pub.sendMessage('MATCHING_DATA_CHANGED',
                        lmd=self.line_matching_data[self.matrix_nr])

    def on_next_matrix(self, item):
        if self.matrix_nr > 0:
            self.matrix_nr -= 1
        else:
            self.matrix_nr = len(self.line_matching_data) - 1

        self.update_line_matching_data()
        pub.sendMessage('MATCHING_DATA_CHANGED',
                        lmd=self.line_matching_data[self.matrix_nr])

    def on_start_direction_changed(self, item):
        print("Not yet implemented")
        tree_iter = item.get_active_iter()
        if tree_iter is not None:
            model = item.get_model()
            row_id, ori = model[tree_iter][:2]
            print("Selected: ORI=%d, descr=%s" % (row_id, ori))
        else:
            entry = item.get_child()
            print("Entered: %s" % entry.get_text())

    def on_start_character_changed(self, item):
        print("Not yet implemented")

    def on_create_new_matrix(self, item):
        print("Not yet implemented")

    def on_refresh(self, item):
        print("Not yet implemented")

    def on_save_clicked(self, item):
        print("Not yet implemented")


class MatrixView(Gtk.Frame):

    def __init__(self, lmd):

        super(MatrixView, self).__init__()

        self._surface = None
        self._hover_pos = Pos(0, 0)

        self.init_line_matching_data(lmd)

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

        self._cursor_on = True
        self._hover_pos = Pos(0, 0)

        # https://developer.gnome.org/gtk3/stable/GtkWidget.html#gtk-widget-add-tick-callback
        self.start_time = time.time()
        self.cursor_callback = self._drawing_area.add_tick_callback(self.toggle_cursor)

        pub.subscribe(self.on_matching_data_changed, 'MATCHING_DATA_CHANGED')

    def init_surface(self, area):
        """Initialize Cairo surface."""
        if self._surface is not None:
            # destroy previous buffer
            self._surface.finish()
            self._surface = None

        # create a new buffer
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())

    def init_line_matching_data(self, lmd):
        self._matrix = lmd.pattern
        self._start_char = lmd.char
        self._start_ori = lmd.ori

    def on_configure(self, area, event, data=None):
        self.init_surface(self._drawing_area)

        context = cairo.Context(self._surface)

        self.do_drawing(context)
        self._surface.flush()

        return False

    def on_matching_data_changed(self, lmd):
        self.init_line_matching_data(lmd)

    def on_button_press(self, widget, event):
        print("Not yet implemented")

    def on_key_press(self, button):
        print("Not yet implemented")

    def on_hover(self, widget, event):
        self._hover_pos = self.calc_position(event.x, event.y)
        # offset = Pos(event.x, event.y) - self._drag_startpos
        self.queue_resize()

    def on_draw(self, area, ctx):
        if self._surface is not None:
            ctx.set_source_surface(self._surface, 0.0, 0.0)
            ctx.paint()
        else:
            print(_("Invalid surface"))
        return False

    def do_drawing(self, ctx):
        self.draw_gridlines(ctx)
        self.draw_content(ctx)
        self.draw_cursor(ctx)

    def draw_gridlines(self, ctx):
        grid_w = Preferences.values['GRIDSIZE_W']
        grid_h = Preferences.values['GRIDSIZE_H']

        x_offset = (self._surface.get_width() - 3 * grid_w) / 2
        y_offset = (self._surface.get_height() - 3 * grid_h) / 2

        # draw a background
        ctx.set_source_rgb(0.95, 0.95, 0.85)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        ctx.new_path()
        ctx.rectangle(x_offset, y_offset, 3 * grid_w, 3 * grid_h)
        ctx.fill()

        # draw the gridlines
        # TODO use CSS for uniform colors?
        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max = x_offset + 3 * grid_w
        y_max = y_offset + 3 * grid_h

        # horizontal lines
        y = y_offset
        for count in range(4):
            ctx.new_path()
            ctx.move_to(x_offset, y)
            ctx.line_to(x_max, y)
            ctx.stroke()
            y += grid_h

        # vertical lines
        x = x_offset
        for count in range(4):
            ctx.new_path()
            ctx.move_to(x, y_offset)
            ctx.line_to(x, y_max)
            ctx.stroke()
            x += grid_w

    def draw_content(self, ctx):

        if self._matrix is None:
            return

        grid_w = Preferences.values['GRIDSIZE_W']
        grid_h = Preferences.values['GRIDSIZE_H']

        x_offset = (self._surface.get_width() - 3 * grid_w) / 2
        y_offset = (self._surface.get_height() - 3 * grid_h) / 2

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

        y = y_offset
        for r in self._matrix:

            x = x_offset
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

    def draw_cursor(self, ctx):

        ctx.save()

        ctx.set_line_width(1.5)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        if self._cursor_on:
            ctx.set_source_rgb(0.75, 0.75, 0.75)
        else:
            ctx.set_source_rgb(0.5, 0.5, 0.5)

        x = self._hover_pos.x
        y = self._hover_pos.y

        ctx.rectangle(x, y, Preferences.values['GRIDSIZE_W'], Preferences.values['GRIDSIZE_H'])
        ctx.stroke()

        ctx.restore()

    def toggle_cursor(self, widget, frame_clock, user_data=None):

        now = time.time()
        elapsed = now - self.start_time

        if elapsed > 0.5:
            self.start_time = now
            self._cursor_on = not self._cursor_on

        self._drawing_area.queue_resize()

        return GLib.SOURCE_CONTINUE

    def calc_position(self, x, y):
        """Calculate the grid view position."""
        pos = Pos(x, y)
        pos.snap_to_grid()
        return pos
