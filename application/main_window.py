"""
AACircuit
2020-03-02 JvO
"""

import sys
import time
from pubsub import pub
from threading import Timer

import gettext

from application import get_path_to_data
from application import ERROR, INFO
from application import INSERT, REMOVE
from application.symbol import Line
from application.grid_view import GridView
from application.component_view import ComponentView
from application.preferences import Preferences, PreferencesDialog
from application.magic_line_settings import MagicLineSettingsDialog

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

        https://eeperry.wordpress.com/2013/01/05/pygtk-new-style-python-class-using-builder/
        """
        try:
            gettext.bindtextdomain('aacircuit', get_path_to_data('locale/'))
            gettext.textdomain('aacircuit')

            builder = Gtk.Builder()
            # https://stackoverflow.com/questions/24320502/how-to-translate-pygtk-glade-gtk-builder-application
            builder.set_translation_domain('aacircuit')
            builder.add_from_file(get_path_to_data('aacircuit.glade'))

        except IOError:
            _ = gettext.gettext
            print(_("Failed to load XML GUI file aacircuit.glade"))
            sys.exit(1)

        new_object = builder.get_object('main_window')
        new_object.finish_initializing(builder)

        return new_object

    def finish_initializing(self, builder):
        """
        Treat this as the __init__() method.
        Arguments pass in must be passed from __new__().
        """
        self.builder = builder
        self.set_default_size(640, 700)

        # Add any other initialization here

        # https://stackoverflow.com/questions/14983385/why-css-style-dont-work-on-gtkbutton
        css_provider = Gtk.CssProvider()

        # https://stackoverflow.com/questions/16740949/gtk-cssprovider-how-do-id-based-selectors-work-in-gtk3
        css_provider.load_from_path(get_path_to_data('style.css'))

        screen = Gdk.Screen.get_default()
        style_context = Gtk.StyleContext()
        style_context.add_provider_for_screen(screen, css_provider,
                                              Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION)

        # statusbar
        self.timer_is_running = False
        self.label_xpos = self.builder.get_object('x_pos')
        self.label_ypos = self.builder.get_object('y_pos')
        self.label_orientation = self.builder.get_object('symbol_orientation')
        self.msg = self.builder.get_object('statusbar1')

        # the GUI signals are handled by this class
        # NB change signals (in Glade) when changing (handler) method names
        self.builder.connect_signals(self)

        # cursor buttons
        self.btn_cur = [
            self.builder.get_object('cursor1'),
            self.builder.get_object('cursor2'),
            self.builder.get_object('cursor3'),
            self.builder.get_object('cursor4')]

        self.text_entry = self.builder.get_object('text_entry')

        # file menu
        self.menu_save = builder.get_object('save_file')
        self.menu_save.set_sensitive(False)

        # edit menu
        self.menu_copy = builder.get_object('copy')
        self.menu_cut = builder.get_object('cut')
        self.menu_paste = builder.get_object('paste')
        self.menu_undo = builder.get_object('undo')
        self.menu_redo = builder.get_object('redo')
        self.menu_copy.set_sensitive(False)
        self.menu_cut.set_sensitive(False)
        self.menu_paste.set_sensitive(False)
        self.menu_undo.set_sensitive(False)
        self.menu_redo.set_sensitive(False)

        # symbol menu
        self.menu_rotate = builder.get_object('rotate_symbol')
        self.menu_mirror = builder.get_object('mirror_symbol')
        self.menu_rotate.set_sensitive(False)
        self.menu_mirror.set_sensitive(False)

        self.connect('delete_event', self.on_delete_window)
        self.connect('destroy', lambda w: Gtk.main_quit())

        self._last_msg_type = None
        self._last_msg_id = None
        self._start_time = time.time()

        self.init_grid()
        self.init_cursors()
        self.init_components()
        self.init_char_buttons()

        # self.start_timer()

        self._undo_stack_empty = True
        pub.subscribe(self.on_pointer_moved, 'POINTER_MOVED')
        pub.subscribe(self.on_message, 'STATUS_MESSAGE')
        pub.subscribe(self.on_orientation_changed, 'ORIENTATION_CHANGED')
        pub.subscribe(self.on_file_opened, 'FILE_OPENED')
        pub.subscribe(self.on_new_file, 'NEW_FILE')
        pub.subscribe(self.on_nothing_selected, 'NOTHING_SELECTED')
        pub.subscribe(self.on_symbol_selected, 'SYMBOL_SELECTED')
        pub.subscribe(self.on_selection_changed, 'SELECTION_CHANGED')
        pub.subscribe(self.on_undo_changed, 'UNDO_CHANGED')
        pub.subscribe(self.on_redo_changed, 'REDO_CHANGED')

    def start_timer(self):
        # FIXME Timer interferes with test (lock.acquire() in shutdown)
        if not self.timer_is_running:
            self._timer = Timer(15, self._timer_event)
            self._timer.start()
            self.timer_is_running = True

    def stop_timer(self):
        self._timer.cancel()
        self.timer_is_running = False

    def _timer_event(self):
        """Clear status message."""
        self.timer_is_running = False
        self.msg.push(0, '')
        self.start_timer()

    def init_components(self):
        component_canvas = ComponentView(self.builder)  # noqa F841

    def init_grid(self):
        fixed = self.builder.get_object('grid_viewport')
        self.grid_view = GridView()
        fixed.add(self.grid_view)

    def init_cursors(self):
        self.cursor = []
        for i in range(1, 5):
            self.cursor.append(GdkPixbuf.Pixbuf.new_from_file(get_path_to_data('buttons/c{0}.png'.format(i))))

    def init_char_buttons(self):
        container = self.builder.get_object('char_table')
        children = container.get_children()
        for btn in children:
            btn.connect('pressed', self.on_char_button_clicked)

    def on_pointer_moved(self, pos):
        """Update the pointer position in the statusbar."""
        self.label_xpos.set_text(format(pos.x))
        self.label_ypos.set_text(format(pos.y))

    def on_orientation_changed(self, ori):
        """Show the Symbol orientation in the statusbar."""
        self.label_orientation.set_label(ori)

    def on_pickpoints_changed(self, item):
        name = Gtk.Buildable.get_name(item)
        state = item.get_active()
        nr = int(name[-1])
        if nr == 1:
            pub.sendMessage('SHOW_SYMBOL_PICKPOINTS', state=state)
        if nr == 2:
            pub.sendMessage('SHOW_LINE_PICKPOINTS', state=state)
        if nr == 3:
            pub.sendMessage('SHOW_TEXT_PICKPOINTS', state=state)

    def on_message(self, msg, type=INFO):
        """
        Add message to statusbar.
        Error messages are shown at least x seconds.
        """
        now = time.time()
        elapsed = now - self._start_time
        if self._last_msg_type != ERROR or elapsed > 5:
            # self.msg.set_css_name('error')
            self.msg.set_name(type)  # use this name in CSS selector (!)
            self._start_time = now
            self._last_msg_type = type
            id = self.msg.get_context_id(msg)
            self._last_msg_id = id
            self.msg.push(id, msg)
            # TODO show errors with another bg color

    def on_add_text(self, button):
        pub.sendMessage('ADD_TEXT')

    def on_add_textblock(self, button):
        text = self.text_entry.get_text()
        pub.sendMessage('ADD_TEXTBLOCK', text=text)

    def on_rotate(self, button):
        pub.sendMessage('ROTATE_SYMBOL')

    def on_mirror(self, button):
        pub.sendMessage('MIRROR_SYMBOL')

    def on_line(self, button):
        name = Gtk.Buildable.get_name(button)
        line = int(name[-1])
        if line == 1:
            type = Line.LINE1
        elif line == 2:
            type = Line.LINE2
        elif line == 3:
            type = Line.LINE3
        elif line == 4:
            type = Line.LINE4
        else:
            type = Line.LINE1
        # DRAW_LINEx
        pub.sendMessage(name.upper(), type=type)

    def on_mag_line(self, button):
        pub.sendMessage('DRAW_MAG_LINE')

    def on_rect(self, button):
        pub.sendMessage('DRAW_RECT')

    def on_arrow(self, button):
        pub.sendMessage('DRAW_ARROW')

    def on_cursor_toggled(self, button):
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
        pub.sendMessage('CHARACTER_CHANGED', char=char)

    def on_delete_window(self, window, event):
        # self.stop_timer()
        return not self.on_close_clicked()

    def on_close_clicked(self, item=None):
        _ = gettext.gettext
        if self._undo_stack_empty or self.show_confirmation_dlg():
            print(_("Closing application"))
            Gtk.main_quit()
        else:
            return False

    def show_confirmation_dlg(self):
        # https://bytes.com/topic/python/answers/873799-how-click-close-window-dont-close-gtk-window
        builder = Gtk.Builder()
        builder.add_from_file(get_path_to_data('confirmation_dialog.glade'))
        builder.connect_signals(self)
        confirm = builder.get_object('confirm')
        result = confirm.run()
        confirm.destroy()
        if result == Gtk.ResponseType.YES:
            return True
        else:
            return False

    def on_select_rect(self, button):
        pub.sendMessage('SELECT_RECT')

    def on_select_space(self, button):
        size = (1, 1)
        pub.sendMessage('ERASER', size=size)

    def on_selecting_eraser(self, button):
        pub.sendMessage('SELECTING_ERASER')

    def on_select_object(self, button):
        pub.sendMessage('SELECT_OBJECT')

    def on_selecting_col(self, button):
        # https://stackoverflow.com/questions/3489520/python-gtk-widget-name
        name = Gtk.Buildable.get_name(button)
        if name == 'insert_col':
            action = INSERT
        else:
            action = REMOVE
        pub.sendMessage('NOTHING_SELECTED')
        pub.sendMessage('SELECTING_COL', action=action)

    def on_selecting_row(self, button):
        name = Gtk.Buildable.get_name(button)
        if name == 'insert_row':
            action = INSERT
        else:
            action = REMOVE
        pub.sendMessage('NOTHING_SELECTED')
        pub.sendMessage('SELECTING_ROW', action=action)

    def on_copy_grid(self, item):
        pub.sendMessage('COPY_GRID')

    def on_paste_grid(self, item):
        pub.sendMessage('PASTE_GRID')

    def on_load_and_paste_grid(self, item):
        pub.sendMessage('LOAD_AND_PASTE_GRID')

    def custom_cursor(self, btn):
        display = self.get_root_window().get_display()
        pb = self.cursor[btn - 1]
        # the cursor hot-spot is at the center of the (16x16) cursor image
        cursor = Gdk.Cursor.new_from_pixbuf(display, pb, 8, 8)
        self.grid_view.get_window().set_cursor(cursor)

    # MENU handling

    def on_menu_file(self, item):
        name = Gtk.Buildable.get_name(item).upper()
        pub.sendMessage(name)

    def on_file_opened(self):
        # enable File menu 'save' when a file has been opened
        self.menu_save.set_sensitive(True)

    def on_new_file(self):
        self.menu_save.set_sensitive(False)

    def on_menu_edit(self, item):
        # cut|copy|paste
        name = Gtk.Buildable.get_name(item)
        # get the rectangle (ul and br have been set in drag begin/end)
        ul, br = self.grid_view.drag_rect
        pub.sendMessage(name.upper(), rect=(ul, br))

    def on_menu_symbol(self, item):
        name = Gtk.Buildable.get_name(item)
        pub.sendMessage(name.upper())

    def on_menu_about(self, item):
        builder = Gtk.Builder()
        builder.add_from_file(get_path_to_data('about_dialog.glade'))
        builder.connect_signals(self)
        about = builder.get_object('about')
        about.set_transient_for(self)
        about.set_modal(True)
        about.run()
        about.destroy()

    def on_menu_preferences(self, item):
        dialog = PreferencesDialog()
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.run()
        dialog.destroy()

    def on_menu_magic_line_settings(self, item):
        dialog = MagicLineSettingsDialog()
        dialog.set_transient_for(self)
        dialog.set_modal(True)
        dialog.run()
        dialog.destroy()

    def on_menu_edit_memo(self, item):
        pub.sendMessage('EDIT_MEMO')

    def on_menu_grid_size(self, item):
        name = Gtk.Buildable.get_name(item)
        # the grid_size option sequence number
        nr = int(name[-1])
        if nr == 1:
            cols, rows = (72, 36)
        elif nr == 2:
            cols, rows = (72, 49)
        elif nr == 3:
            cols, rows = (100, 49)
        elif nr == 4:
            cols, rows = (200, 70)
        else:
            # default, catch all
            cols, rows = (Preferences.values['DEFAULT_COLS'], Preferences.values['DEFAULT_ROWS'])
        # strip the sequence nr
        name = name[:-2]
        pub.sendMessage(name.upper(), cols=cols, rows=rows)

    def on_redraw_grid(self, item):
        pub.sendMessage('REDRAW_GRID')

    def on_nothing_selected(self):
        self.on_selection_changed()
        self.menu_rotate.set_sensitive(False)
        self.menu_mirror.set_sensitive(False)

    def on_symbol_selected(self, symbol):
        # enable the Symbol menu options only when a symbol has been selected
        self.menu_rotate.set_sensitive(True)
        self.menu_mirror.set_sensitive(True)

    def on_selection_changed(self, selected=False):
        # enable the cut and copy menu only when one or more objects are selected
        self.menu_copy.set_sensitive(selected)
        self.menu_cut.set_sensitive(selected)

    def on_undo_changed(self, undo=False):
        self._undo_stack_empty = not undo
        # enable undo only if the undo-stack is not empty
        self.menu_undo.set_sensitive(undo)

    def on_redo_changed(self, redo=False):
        # enable redo only if the redo-stack is not empty
        self.menu_redo.set_sensitive(redo)

    def on_undo(self, button):
        name = Gtk.Buildable.get_name(button)
        pub.sendMessage(name.upper())
