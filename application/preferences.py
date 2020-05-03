"""
AACircuit
2020-03-02 JvO
"""

import os
import sys
import locale
import json
import collections
from pubsub import pub
from locale import gettext as _

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402


PreferenceSetting = collections.namedtuple('PreferenceSetting', ['type', 'entry'])


class Preferences(object):

    values = dict()

    # default preference values

    values['DEFAULT_ROWS'] = 36
    values['DEFAULT_COLS'] = 72

    values['FONTSIZE'] = 12
    values['GRIDSIZE_W'] = 10
    values['GRIDSIZE_H'] = 16

    values['PANGO_FONT'] = False
    values['FONT'] = 'monospace'

    # draw selection by dragging (True) or click and second-click (False)
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

    def __init__(self, filename='aacircuit.ini'):

        self._filename = filename
        self.read_preferences()

        pub.subscribe(self.on_save_preferences, 'SAVE_PREFERENCES')

    def has_value(self, name):
        """Verify whether we have a preference value with this name."""

        try:
            value = self.values[name]  # noqa F841
            return True

        except KeyError:
            return False

    def nr_values(self):
        """Return the number of preference settings."""
        return len(self.values)

    def get_value(self, name):
        """
        Return value with the given preference name.
        Deprecated method.
        Use the class dictionary instead: value = Preferences.values['name']
        """

        print("Deprecated method: ", self.get_value.__name__)

        try:
            return self.values[name]

        except KeyError:
            print("Unknown preference name", name)
            raise KeyError

    def set_pref(self, name, value):
        """Set the value for preference with the given name."""
        self.values[name] = value

    def read_preferences(self):

        try:
            file = open(self._filename, 'r')
            str = file.read()
            file.close()

            Preferences.values = json.loads(str)

            msg = _("Preferences have been read from: %s" % self._filename)
            # pub.sendMessage('STATUS_MESSAGE', msg=msg)
            print(msg)

        except IOError:
            msg = _("Preferences file not found: %s, default preferences are being used" % self._filename)
            # pub.sendMessage('STATUS_MESSAGE', msg=msg)
            print(msg)

    def on_save_preferences(self):

        try:
            fout = open(self._filename, 'w')

            str = json.dumps(Preferences.values)

            fout.write(str)
            fout.close()

            msg = _("Preferences have been saved in: %s" % self._filename)
            pub.sendMessage('STATUS_MESSAGE', msg=msg)

        except IOError:
            msg = _("Unable to open file for writing: %s" % self._filename)
            pub.sendMessage('STATUS_MESSAGE', msg=msg)


class NumberEntry(Gtk.Entry):

    def __init__(self):
        Gtk.Entry.__init__(self)
        self.set_alignment(0.5)  # center
        self.connect('changed', self.on_changed)

    def on_changed(self, *args):
        text = self.get_text().strip()
        self.set_text(''.join([i for i in text if i in '0123456789']))


class SingleCharEntry(Gtk.Entry):

    def __init__(self):
        Gtk.Entry.__init__(self)
        # self.set_width_chars(2)
        self.set_alignment(0.5)  # center
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

        self.entries = dict()

        frame = builder.get_object('grid')
        self.init_grid_prefs(frame)

        frame = builder.get_object('lines')
        self.init_lines_prefs(frame)

        frame = builder.get_object('magic_line')
        self.init_magic_line_prefs(frame)

        self.show_all()

    def entry_string(self, container, row, label_txt, name):

        label = Gtk.Label(label_txt)
        label.set_alignment(0, 0)
        container.attach(label, 0, row, 1, 1)

        entry = SingleCharEntry()
        value = str(Preferences.values[name])
        entry.set_text(value)
        container.attach(entry, 1, row, 1, 1)

        self.entries[name] = PreferenceSetting('str', entry)

    def entry_dimension(self, container, row, label_txt, name):

        label = Gtk.Label(label_txt)
        label.set_alignment(0, 0)
        container.attach(label, 0, row, 1, 1)

        entry = NumberEntry()
        value = str(Preferences.values[name])
        entry.set_text(value)

        container.attach(entry, 1, row, 1, 1)

        self.entries[name] = PreferenceSetting('dim', entry)

    def entry_font(self, container, row, label_txt, name):

        label = Gtk.Label(label_txt)
        label.set_alignment(0, 0)
        container.attach(label, 0, row, 1, 1)

        entry = Gtk.FontButton()
        value = str(Preferences.values[name])
        entry.set_font_name(value)
        container.attach(entry, 1, row, 1, 1)

        self.entries[name] = PreferenceSetting('font', entry)

    def entry_bool(self, container, row, label_txt, name):

        label = Gtk.Label(label_txt)
        label.set_alignment(0, 0)
        container.attach(label, 0, row, 1, 1)

        entry = Gtk.CheckButton()
        value = Preferences.values[name]
        entry.set_active(value)
        container.attach(entry, 1, row, 1, 1)

        self.entries[name] = PreferenceSetting('bool', entry)

    def init_grid_prefs(self, frame):

        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        frame.add(grid)

        row = 0
        self.entry_dimension(grid, row, _("Number of rows"), 'DEFAULT_ROWS')
        row += 1
        self.entry_dimension(grid, row, _("Number of columns"), 'DEFAULT_COLS')
        row += 1
        self.entry_dimension(grid, row, _("cell width"), 'GRIDSIZE_W')
        row += 1
        self.entry_dimension(grid, row, _("cell height"), 'GRIDSIZE_H')
        row += 1
        self.entry_dimension(grid, row, _("Font size"), 'FONTSIZE')
        row += 1
        self.entry_bool(grid, row, _("Use Pango font"), 'PANGO_FONT')
        row += 1
        self.entry_font(grid, row, _("Font"), 'FONT')
        row += 1
        # in effect after closing/opening application
        self.entry_bool(grid, row, _("Drag selection"), 'SELECTION_DRAG')

    def init_lines_prefs(self, frame):

        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        frame.add(grid)

        row = 0
        self.entry_string(grid, row, _("Horizontal line char"), 'LINE_HOR')
        row += 1
        self.entry_string(grid, row, _("Vertical line char"), 'LINE_VERT')
        row += 1
        self.entry_string(grid, row, _("Terminal char 1"), 'TERMINAL1')
        row += 1
        self.entry_string(grid, row, _("Terminal char 2"), 'TERMINAL2')
        row += 1
        self.entry_string(grid, row, _("Terminal char 3"), 'TERMINAL3')
        row += 1
        self.entry_string(grid, row, _("Terminal char 4"), 'TERMINAL4')

    def init_magic_line_prefs(self, frame):

        grid = Gtk.Grid()
        grid.set_row_spacing(5)
        grid.set_column_spacing(5)
        frame.add(grid)

        row = 0
        self.entry_string(grid, row, _("Crossing char"), 'CROSSING')
        row += 1
        self.entry_string(grid, row, _("Upper corner char"), 'UPPER_CORNER')
        row += 1
        self.entry_string(grid, row, _("Lower corner char"), 'LOWER_CORNER')

    def on_ok_clicked(self, item):

        for key, setting in self.entries.items():

            if setting.type == 'str':
                value = setting.entry.get_text()

            elif setting.type == 'dim':
                value = int(setting.entry.get_text())

            elif setting.type == 'bool':
                value = setting.entry.get_active()

            elif setting.type == 'font':
                value = setting.entry.get_font_name()

            Preferences.values[key] = value

        pub.sendMessage('SAVE_PREFERENCES')
