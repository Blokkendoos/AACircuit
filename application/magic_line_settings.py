"""
AACircuit
2020-03-02 JvO
"""

import cairo
import time
import json
import copy
import collections
from pubsub import pub

from application import get_path_to_data
from application import LONGEST_FIRST, HORIZONTAL, VERTICAL
from application.pos import Pos
from application.preferences import Preferences, SingleCharEntry

import sys
import locale
from locale import gettext as _

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo  # noqa: E402


LineMatchingData = collections.namedtuple('line_matching_data', ['pattern', 'ori', 'char'])


class MagicLineSettings(object):

    LMD = []

    def __init__(self, filename='magic_line.ini'):
        self._filename = filename
        self.read_settings()
        pub.subscribe(self.on_save_settings, 'SAVE_MAGIC_LINE_SETTINGS')
        pub.subscribe(self.load_default_settings, 'RESTORE_DEFAULT_MAGIC_LINE_SETTINGS')

    def read_settings(self):
        try:
            file = open(self._filename, 'r')
            self.load_settings_from_str(file.read())
            file.close()

            msg = _("Magic_line settings have been read from: %s" % self._filename)
            print(msg)

        except IOError:
            self.load_default_settings()
            msg = _("Magic line default settings are being used")
            # pub.sendMessage('STATUS_MESSAGE', msg=msg)
            print(msg)

    def on_save_settings(self):
        try:
            fout = open(self._filename, 'w')
            fout.write(self.settings_to_str())
            fout.close()

            msg = _("Magic line settings have been saved in: %s" % self._filename)
            pub.sendMessage('STATUS_MESSAGE', msg=msg)

        except IOError:
            msg = _("Unable to open file for writing: %s" % self._filename)
            pub.sendMessage('STATUS_MESSAGE', msg=msg)

    def settings_to_str(self):
        str = ""

        for lmd in self.LMD:
            lmd_dict = dict()
            lmd_dict['pattern'] = lmd.pattern
            lmd_dict['ori'] = lmd.ori
            lmd_dict['char'] = lmd.char
            str += json.dumps(lmd_dict) + '\n'

        return str

    def load_settings_from_str(self, str):
        MagicLineSettings.LMD = []
        for line in str.splitlines():
            item = json.loads(line)
            lmd = LineMatchingData(item['pattern'], item['ori'], item['char'])
            MagicLineSettings.LMD.append(lmd)

    def load_default_settings(self):
        lmd = []
        lmd.append(LineMatchingData(
            [[' ', ' ', ' '],
             [' ', ' ', ' '],
             [' ', ' ', ' ']], LONGEST_FIRST, 'o'))
        lmd.append(LineMatchingData(
            [['x', 'x', 'x'],
             ['-', 'x', '-'],
             ['x', 'x', 'x']], VERTICAL, 'o'))
        lmd.append(LineMatchingData(
            [['x', '|', 'x'],
             ['x', 'x', 'x'],
             ['x', '|', 'x']], HORIZONTAL, 'o'))
        lmd.append(LineMatchingData(
            [['x', 'x', 'x'],
             ['x', 'x', '-'],
             ['x', 'x', 'x']], HORIZONTAL, '-'))
        lmd.append(LineMatchingData(
            [['x', 'x', 'x'],
             ['-', 'x', 'x'],
             ['x', 'x', 'x']], HORIZONTAL, '-'))
        lmd.append(LineMatchingData(
            [['x', 'x', 'x'],
             ['x', 'x', 'x'],
             [' ', '|', ' ']], VERTICAL, '|'))
        lmd.append(LineMatchingData(
            [[' ', '|', ' '],
             ['x', 'x', 'x'],
             ['x', 'x', 'x']], VERTICAL, '|'))
        lmd.append(LineMatchingData(
            [['x', 'x', 'x'],
             ['x', 'x', 'x'],
             ['x', '|', 'x']], HORIZONTAL, '.'))
        lmd.append(LineMatchingData(
            [['x', '|', 'x'],
             ['x', 'x', 'x'],
             ['x', 'x', 'x']], HORIZONTAL, "'"))
        lmd.append(LineMatchingData(
            [['x', 'x', 'x'],
             ['x', '|', 'x'],
             ['x', 'x', 'x']], VERTICAL, '|'))

        MagicLineSettings.LMD = lmd


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
            builder.add_from_file(get_path_to_data('magic_line_dialog.glade'))

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
        # self.set_default_size(400, 250)

        # Add any other initialization here

        self.matrix_nr = 0
        self.lmd = copy.deepcopy(MagicLineSettings.LMD)

        self.init_matrix_view(builder)
        self.init_start_orientation(builder)
        self.init_start_character(builder)
        self.update_line_matching_data()

        self.show_all()

    def init_start_orientation(self, builder):
        # orientation and description
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
        self._start_character = start_character
        self._start_character.connect('changed', self.on_start_character_changed)

    def update_line_matching_data(self):
        lmd = self.lmd[self.matrix_nr]
        self._start_character.set_text(lmd.char)
        self._start_ori_combo.set_active(lmd.ori)

    def init_matrix_view(self, builder):
        view = builder.get_object('matrix_viewport')
        self.matrix_view = MatrixView(self.lmd, self.matrix_nr)
        view.add(self.matrix_view)

    def on_previous_matrix(self, item):
        self.matrix_nr += 1
        self.matrix_nr %= len(self.lmd)

        self.update_line_matching_data()
        pub.sendMessage('MATCHING_DATA_CHANGED', mnr=self.matrix_nr)

    def on_next_matrix(self, item):
        if self.matrix_nr > 0:
            self.matrix_nr -= 1
        else:
            self.matrix_nr = len(self.lmd) - 1

        self.update_line_matching_data()
        pub.sendMessage('MATCHING_DATA_CHANGED', mnr=self.matrix_nr)

    def on_start_direction_changed(self, item):
        tree_iter = item.get_active_iter()
        if tree_iter is not None:
            model = item.get_model()
            ori, description = model[tree_iter][:2]
            # print("Selected: ori=%d, descr=%s" % (ori, description))

            lmd = self.lmd[self.matrix_nr]
            lmd_new = LineMatchingData(lmd.pattern, ori, lmd.char)
            self.lmd[self.matrix_nr] = lmd_new

    def on_start_character_changed(self, item):
        char = item.get_text()
        lmd = self.lmd[self.matrix_nr]
        if lmd.char != char:
            lmd_new = LineMatchingData(lmd.pattern, lmd.ori, char)
            self.lmd[self.matrix_nr] = lmd_new

    def on_create_new_matrix(self, item):
        print("Not yet implemented")

    def on_save_clicked(self, item):
        MagicLineSettings.LMD = self.lmd
        pub.sendMessage('SAVE_MAGIC_LINE_SETTINGS')

    def on_restore_defaults_clicked(self, item):
        pub.sendMessage('RESTORE_DEFAULT_MAGIC_LINE_SETTINGS')
        self.lmd = copy.deepcopy(MagicLineSettings.LMD)
        self.update_line_matching_data()
        pub.sendMessage('MATCHING_DATA_CHANGED', mnr=self.matrix_nr)


class MatrixView(Gtk.DrawingArea):

    def __init__(self, lmd, mnr=0):
        super(MatrixView, self).__init__()

        self._surface = None
        self._hover_pos = Pos(0, 0)

        self.set_can_focus(True)
        self.set_focus_on_click(True)

        self.connect('draw', self.on_draw)
        self.connect('configure-event', self.on_configure)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self.on_button_press)

        # https://stackoverflow.com/questions/44098084/how-do-i-handle-keyboard-events-in-gtk3
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key-press-event', self.on_key_press)

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('motion-notify-event', self.on_hover)

        self._cursor_on = True
        self._hover_pos = Pos(0, 0)

        # line matching data
        self._lmd = lmd
        self._matrix_nr = mnr
        self.set_line_matching_data()

        # https://developer.gnome.org/gtk3/stable/GtkWidget.html#gtk-widget-add-tick-callback
        self.start_time = time.time()
        self.cursor_callback = self.add_tick_callback(self.toggle_cursor)

        pub.subscribe(self.on_matching_data_changed, 'MATCHING_DATA_CHANGED')

    def init_surface(self, area):
        """Initialize Cairo surface."""
        if self._surface is not None:
            # destroy previous buffer
            self._surface.finish()
            self._surface = None

        # create a new buffer
        self._surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())

    def set_line_matching_data(self):
        lmd = self._lmd[self._matrix_nr]
        self._matrix = lmd.pattern
        self._start_char = lmd.char
        self._start_ori = lmd.ori

    def calc_offset(self):
        """Calculate the upper left coordinate where the matrix will be drawn."""
        grid_w = Preferences.values['GRIDSIZE_W']
        grid_h = Preferences.values['GRIDSIZE_H']

        x_offset = round((self._surface.get_width() - 3 * grid_w) / 2)
        y_offset = round((self._surface.get_height() - 3 * grid_h) / 2)

        self._offset = Pos(x_offset, y_offset)
        self._offset.snap_to_grid()

    def on_configure(self, area, event, data=None):
        self.init_surface(self)
        self.calc_offset()

        context = cairo.Context(self._surface)

        self.do_drawing(context)
        self._surface.flush()

        return False

    def on_matching_data_changed(self, mnr):
        self._matrix_nr = mnr
        self.set_line_matching_data()

    def on_button_press(self, button, event):
        return True

    def on_key_press(self, widget, event):
        # TODO Will this work in other locale too?
        def filter_non_printable(ascii):
            char = ''
            if (ascii > 31 and ascii < 255) or ascii == 9:
                char = chr(ascii)
            return char

        def valid_index(pos):
            if pos.x >= 0 and pos.x < 3 and pos.y >= 0 and pos.y < 3:
                return True
            else:
                return False

        def next_char():
            # move to the next character or the next line
            if grid_pos.x < 2:
                self._hover_pos += Pos(1, 0).view_xy()
            elif grid_pos.y < 2:
                self._hover_pos += Pos(-2, 1).view_xy()

        def previous_char():
            # move to the previous character or the previous line
            if grid_pos.x > 0:
                if grid_pos.x <= 2:
                    self._hover_pos -= Pos(1, 0).view_xy()
            elif grid_pos.y > 0:
                self._hover_pos += Pos(2, -1).view_xy()

        value = event.keyval

        grid_pos = self._hover_pos - self._offset
        grid_pos.snap_to_grid()
        grid_pos = grid_pos.grid_cr()

        # shift = (event.state & Gdk.ModifierType.SHIFT_MASK)
        # modifiers = Gdk.Accelerator.get_default_mod_mask()
        shift = event.state & Gdk.ModifierType.SHIFT_MASK
        if shift:
            return True

        if value == Gdk.KEY_Left or value == Gdk.KEY_BackSpace:
            previous_char()

        elif value == Gdk.KEY_Right:
            next_char()

        elif value == Gdk.KEY_Up:
            self._hover_pos -= Pos(0, 1).view_xy()

        elif value == Gdk.KEY_Down:
            self._hover_pos += Pos(0, 1).view_xy()

        elif value & 255 != 13:  # enter

            if valid_index(grid_pos):
                str = filter_non_printable(value)
                self._matrix[grid_pos.y][grid_pos.x] = str
                next_char()

        return True

    def on_hover(self, widget, event):
        if not self.has_focus():
            self.grab_focus()

        self._hover_pos = Pos(event.x, event.y)
        self._hover_pos.snap_to_grid()
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

        offset = self._offset

        # draw a background
        ctx.set_source_rgb(0.95, 0.95, 0.85)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        ctx.new_path()
        ctx.rectangle(offset.x, offset.y, 3 * grid_w, 3 * grid_h)
        ctx.fill()

        # draw the gridlines
        # TODO use CSS for uniform colors?
        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max = offset.x + 3 * grid_w
        y_max = offset.y + 3 * grid_h

        # horizontal lines
        y = offset.y
        for count in range(4):
            ctx.new_path()
            ctx.move_to(offset.x, y)
            ctx.line_to(x_max, y)
            ctx.stroke()
            y += grid_h

        # vertical lines
        x = offset.x
        for count in range(4):
            ctx.new_path()
            ctx.move_to(x, offset.y)
            ctx.line_to(x, y_max)
            ctx.stroke()
            x += grid_w

    def draw_content(self, ctx):
        if self._matrix is None:
            return

        grid_w = Preferences.values['GRIDSIZE_W']
        grid_h = Preferences.values['GRIDSIZE_H']

        offset = self._offset

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

        y = offset.y
        for r in self._matrix:

            x = offset.x
            for c in r:

                if use_pango_font:
                    ctx.move_to(x, y)
                    layout.set_text(str(c), -1)
                    PangoCairo.show_layout(ctx, layout)
                else:
                    # the Cairo text glyph origin is its left-bottom corner
                    ctx.move_to(x, y + Preferences.values['FONTSIZE'])
                    ctx.show_text(str(c))

                x += grid_w

            y += grid_h

    def draw_cursor(self, ctx):
        if not self.has_focus():
            return

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

        self.queue_resize()

        return GLib.SOURCE_CONTINUE
