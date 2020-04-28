"""
AACircuit
2020-03-02 JvO
"""

import os
import sys
import json
import locale
from locale import gettext as _

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402


class Preferences(object):

    values = dict()

    values['DEFAULT_ROWS'] = 36
    values['DEFAULT_COLS'] = 72

    values['FONTSIZE'] = 12
    values['GRIDSIZE_W'] = 10
    values['GRIDSIZE_H'] = 16

    # draw selection by dragging or click and second-click
    values['SELECTION_DRAG'] = False

    values['LINE_HOR'] = '-'
    values['LINE_VERT'] = '|'
    values['CROSSING'] = ')'

    values['LOWER_CORNER'] = "'"
    values['UPPER_CORNER'] = '.'

    values['TERMINAL1'] = None
    values['TERMINAL2'] = 'o'
    values['TERMINAL3'] = '+'
    values['TERMINAL4'] = "'"

    def __init__(self, prefs=None):
        if prefs:
            self.values = json.loads(prefs)

    def get_all_prefs(self):
        return json.dumps(self.values)

    def get_value(self, name):
        try:
            return self.values[name]
        except KeyError:
            print("Unknown preference name", name)
            raise KeyError

    def set_pref(self, name, value):
        self.values[name] = value


class NumberEntry(Gtk.Entry):

    def __init__(self):
        Gtk.Entry.__init__(self)
        self.connect('changed', self.on_changed)

    def on_changed(self, *args):
        text = self.get_text().strip()
        self.set_text(''.join([i for i in text if i in '0123456789']))


class SingleCharEntry(Gtk.Entry):

    def __init__(self):
        Gtk.Entry.__init__(self)
        self.connect('changed', self.on_changed)

    def set_text(self, str):
        if str is None:
            str = 'None'
        super(SingleCharEntry, self).set_text(str)

    def on_changed(self, *args):
        text = self.get_text().strip()
        if text != 'None' and len(text) > 1:
            self.set_text(text[1])


class PreferencesDialog(Gtk.Dialog):
    __gtype_name__ = 'PreferencesDialog'

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
            builder.add_from_file(os.path.join(app_path, 'preferences_dialog.glade'))

        except IOError:
            print(_("Failed to load XML GUI file preferences_dialog.glade"))
            sys.exit(1)

        new_object = builder.get_object('preferences')
        new_object.finish_initializing(builder)

        return new_object

    def finish_initializing(self, builder):
        """
        Treat this as the __init__() method.
        Arguments pass in must be passed from __new__().
        """
        builder.connect_signals(self)
        self.set_default_size(350, 600)

        # Add any other initialization here

        # https://stackoverflow.com/questions/14983385/why-css-style-dont-work-on-gtkbutton
        cssProvider = Gtk.CssProvider()
        cssProvider.load_from_path('application/style.css')
        screen = Gdk.Screen.get_default()
        styleContext = Gtk.StyleContext()
        # With the others GTK_STYLE_PROVIDER_PRIORITY values get the same result
        styleContext.add_provider_for_screen(screen, cssProvider,
                                             Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        self.prefs = Preferences()

        frame = builder.get_object('grid')
        self.init_grid_prefs(frame)

        frame = builder.get_object('lines')
        self.init_lines_prefs(frame)

        frame = builder.get_object('magic_line')
        self.init_magic_line_prefs(frame)

        self.show_all()

    def entry_dimension(self, container, label_txt, name, value):

        label = Gtk.Label(label_txt)
        label.set_justify(Gtk.JUSTIFY_LEFT)
        container.pack_start(label, False, True, 0)

        entry = NumberEntry()
        container.pack_start(entry, False, True, 0)
        entry.set_text(str(value))

    def entry_bool(self, container, label_txt, name, value):

        label = Gtk.Label(label_txt)
        container.pack_start(label, False, True, 0)

        entry = Gtk.CheckButton()
        container.pack_start(entry, False, True, 0)
        entry.active = value

    def init_grid_prefs_1(self, builder):

        grid = builder.get_object('grid')
        hbox = Gtk.HBox(spacing=6)
        grid.add(hbox)

        vbox = Gtk.VBox(spacing=6)
        grid.add(vbox)

        box = Gtk.Box(spacing=6)
        vbox.add(box)
        self.entry_dimension(box, _("Number of rows"), 'DEFAULT_ROWS', 36)
        self.entry_dimension(box, _("columns"), 'DEFAULT_COLS', 72)

        box = Gtk.Box(spacing=6)
        vbox.add(box)
        self.entry_dimension(box, _("Cell width"), 'GRIDSIZE_W', 10)
        self.entry_dimension(box, _("height"), 'GRIDSIZE_H', 16)

        box = Gtk.Box(spacing=6)
        vbox.add(box)
        self.entry_dimension(box, _("Font size"), 'FONTSIZE', 12)

        box = Gtk.Box(spacing=6)
        vbox.add(box)
        self.entry_bool(box, _("Select by dragging"), 'SELECTION_DRAG', False)

    def init_grid_prefs(self, frame):

        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        frame.add(grid)

        row = 0

        label = Gtk.Label(_("Number of rows"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = NumberEntry()
        entry.set_text(str(36))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Number of columns"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, 1, 1, 1)

        entry = NumberEntry()
        entry.set_text(str(72))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Font size"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = NumberEntry()
        entry.set_text(str(12))
        grid.attach(entry, 1, row, 1, 1)

    def init_lines_prefs(self, frame):

        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        frame.add(grid)

        row = 0

        label = Gtk.Label(_("Horizontal line char"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('LINE_HOR'))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Vertical line char"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('LINE_VERT'))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Crossing char"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('CROSSING'))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Terminal char 1"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('TERMINAL1'))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Terminal char 2"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('TERMINAL2'))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Terminal char 3"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('TERMINAL3'))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Terminal char 4"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('TERMINAL4'))
        grid.attach(entry, 1, row, 1, 1)

    def init_magic_line_prefs(self, frame):

        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        frame.add(grid)

        row = 0

        label = Gtk.Label(_("Crossing char"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('CROSSING'))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Upper corner char"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('UPPER_CORNER'))
        grid.attach(entry, 1, row, 1, 1)

        row += 1

        label = Gtk.Label(_("Lower corner char"))
        label.set_alignment(0, 0)
        grid.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        entry.set_text(self.prefs.get_value('LOWER_CORNER'))
        grid.attach(entry, 1, row, 1, 1)
