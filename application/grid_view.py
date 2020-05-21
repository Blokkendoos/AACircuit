"""
AACircuit
2020-03-02 JvO
"""

import cairo
import time
from pubsub import pub

from application import _
from application import HORIZONTAL, VERTICAL
from application import IDLE, SELECTING, SELECTED
from application import CHARACTER, COMPONENT, LINE, MAG_LINE, DIR_LINE, OBJECTS, COL, ROW, RECT, DRAW_RECT
from application import MARK_CHAR
from application import TEXT, TEXT_BLOCK
from application.pos import Pos
from application.symbol import Text, Line, MagLine, DirLine, Rect
from application.preferences import Preferences
from application.selection import Selection, SelectionCol, SelectionRow, SelectionRect

import gi

gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib  # noqa: E402

gi.require_version('PangoCairo', '1.0')
from gi.repository import Pango, PangoCairo  # noqa: E402


class GridView(Gtk.DrawingArea):

    def __init__(self):

        super(GridView, self).__init__()

        self.surface = None
        self._grid = None
        self._objects = None
        self._hover_pos = Pos(0, 0)

        self._selection = Selection(None)

        # selection position
        self._drag_dir = None
        self._drag_startpos = None
        self._drag_endpos = None
        self._drag_currentpos = None
        self._drag_prevpos = []

        # text
        self._cursor_on = True
        self._text = ""

        # pickpoints
        self._show_symbol_pickpoints = True
        self._show_line_pickpoints = True
        self._show_text_pickpoints = True

        self.set_can_focus(True)

        self.connect('draw', self.on_draw)
        self.connect('configure-event', self.on_configure)

        self.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.connect('button-press-event', self.on_button_press)

        # https://stackoverflow.com/questions/44098084/how-do-i-handle-keyboard-events-in-gtk3
        self.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self.connect('key-press-event', self.on_key_press)

        if Preferences.values['SELECTION_DRAG']:
            self._gesture_drag = Gtk.GestureDrag.new(self)
            self._gesture_drag.connect('drag-begin', self.on_drag_begin)
            self._gesture_drag.connect('drag-end', self.on_drag_end)
            self._gesture_drag.connect('drag-update', self.on_drag_update)

        self.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.connect('motion-notify-event', self.on_hover)

        # https://developer.gnome.org/gtk3/stable/GtkWidget.html#gtk-widget-add-tick-callback
        self.start_time = time.time()
        self.cursor_callback = self.add_tick_callback(self.toggle_cursor)
        # self.remove_tick_callback(self.cursor_callback)

        # subscriptions

        pub.subscribe(self.set_grid, 'NEW_GRID')

        pub.subscribe(self.on_add_text, 'ADD_TEXT')
        pub.subscribe(self.on_add_textblock, 'ADD_TEXTBLOCK')

        pub.subscribe(self.on_character_selected, 'CHARACTER_SELECTED')
        pub.subscribe(self.on_symbol_selected, 'SYMBOL_SELECTED')
        pub.subscribe(self.on_objects_selected, 'OBJECTS_SELECTED')

        pub.subscribe(self.on_selecting_rect, 'SELECTING_RECT')
        pub.subscribe(self.on_selecting_objects, 'SELECTING_OBJECTS')
        pub.subscribe(self.on_selecting_row, 'SELECTING_ROW')
        pub.subscribe(self.on_selecting_col, 'SELECTING_COL')

        pub.subscribe(self.on_nothing_selected, 'NOTHING_SELECTED')

        pub.subscribe(self.on_draw_mag_line, 'DRAW_MAG_LINE')
        pub.subscribe(self.on_draw_dir_line, 'DRAW_LINE0')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE1')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE2')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE3')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE4')

        pub.subscribe(self.on_draw_rect, 'DRAW_RECT')

        # printing
        pub.subscribe(self.on_begin_print, 'BEGIN_PRINT')
        pub.subscribe(self.on_draw_page, 'DRAW_PAGE')
        pub.subscribe(self.on_draw_pdf, 'DRAW_PDF')

        # pickpoints
        pub.subscribe(self.on_show_symbol_pickpoints, 'SHOW_SYMBOL_PICKPOINTS')
        pub.subscribe(self.on_show_line_pickpoints, 'SHOW_LINE_PICKPOINTS')
        pub.subscribe(self.on_show_text_pickpoints, 'SHOW_TEXT_PICKPOINTS')

    def set_grid(self, grid):
        self._grid = grid
        self.set_viewport_size()

    def set_viewport_size(self):
        # https://stackoverflow.com/questions/11546395/how-to-put-gtk-drawingarea-into-gtk-layout
        width = self._grid.nr_cols * Preferences.values['GRIDSIZE_W']
        height = self._grid.nr_rows * Preferences.values['GRIDSIZE_H']
        self.set_size_request(width, height)

    @property
    def max_pos(self):
        x_max = self.surface.get_width()
        y_max = self.surface.get_height()
        return Pos(x_max, y_max)

    @property
    def max_pos_grid(self):
        x_max = self._grid.nr_cols * Preferences.values['GRIDSIZE_W']
        y_max = self._grid.nr_rows * Preferences.values['GRIDSIZE_H']
        return Pos(x_max, y_max)

    @property
    def drag_rect(self):
        """Return the selected rectangle (upper-left and bottom-right) position."""

        if self._drag_startpos <= self._drag_endpos:
            ul = self._drag_startpos
            br = self._drag_endpos
        else:
            ul = self._drag_endpos
            br = self._drag_startpos

        ul = ul.grid_cr()
        br = br.grid_cr()

        return ul, br

    def init_surface(self, area):
        """Initialize Cairo surface."""
        if self.surface is not None:
            # destroy previous buffer
            self.surface.finish()
            self.surface = None

        # create a new buffer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())

    def on_configure(self, area, event, data=None):
        self.init_surface(self)
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

    # (don't) show pickpoints

    def on_show_symbol_pickpoints(self, state):
        self._show_symbol_pickpoints = state

    def on_show_line_pickpoints(self, state):
        self._show_line_pickpoints = state

    def on_show_text_pickpoints(self, state):
        self._show_text_pickpoints = state

    # printing

    def on_begin_print(self, parms):
        operation, print_ctx = parms

        operation.set_n_pages(1)

    def on_draw_page(self, parms):
        operation, print_ctx, page_num = parms

        w = print_ctx.get_width()
        h = print_ctx.get_height()
        # print("width: {} height:{})".format(w, h))

        ctx = print_ctx.get_cairo_context()

        # self.draw_border(ctx, w, h)
        ctx.scale(0.5, 0.5)
        self.draw_content(ctx)

    def on_draw_pdf(self, filename):

        # don't use the drawing_area, so that this method can be run from (nose) test method (w/o GUI)
        # w = self.get_allocated_width()
        # h = self.get_allocated_height()
        # FIXME Set Portrait or Landscape dimensions based upon prefs or printer settings
        w, h = (560, 784)

        surface = cairo.PDFSurface(filename, w, h)
        ctx = cairo.Context(surface)

        # self.draw_border(ctx, w, h)
        ctx.scale(0.5, 0.5)
        self.draw_content(ctx)

        surface.finish()

        msg = _("PDF Exported to {}").format(filename)
        pub.sendMessage('STATUS_MESSAGE', msg=msg)

    # SELECTIONs

    def on_nothing_selected(self):
        self._selection = Selection(None)
        self.queue_resize()

    def on_add_text(self):
        self._selection = Selection(item=TEXT, state=SELECTING)
        self._text = ""
        self._symbol = Text(Pos(0, 0), self._text)
        self.grab_focus()

    def on_add_textblock(self, text):
        self._selection = Selection(item=TEXT_BLOCK, state=SELECTING)
        self._symbol = Text(Pos(0, 0), text)
        self._text = text

    def on_character_selected(self, char):
        self._selection = Selection(item=CHARACTER, state=SELECTED)
        self._symbol = char

    def on_symbol_selected(self, symbol):
        # only components (can be rotated or mirrored)
        self._selection = Selection(item=COMPONENT, state=SELECTED)
        self._symbol = symbol

    def on_objects_selected(self, objects):
        self._selection = Selection(item=OBJECTS, state=SELECTED)
        self._objects = objects

    def on_selecting_objects(self, objects):
        self._selection = Selection(item=OBJECTS, state=SELECTING)
        self._objects = objects

    def on_selecting_rect(self, objects):
        self._selection = SelectionRect()
        self._objects = objects

    def on_selecting_row(self, action):
        self._selection = SelectionRow(action)

    def on_selecting_col(self, action):
        self._selection = SelectionCol(action)

    # LINES

    def on_draw_mag_line(self):
        self._selection = Selection(item=MAG_LINE)
        self._symbol = MagLine(Pos(0, 0), Pos(1, 1), self._grid.cell)

    def on_draw_dir_line(self, type):
        self._selection = Selection(item=DIR_LINE)
        self._symbol = DirLine(Pos(0, 0), Pos(1, 1))

    def on_draw_line(self, type):
        self._selection = Selection(item=LINE)
        self._symbol = Line(Pos(0, 0), Pos(1, 1), type=type)

    def on_draw_rect(self):
        self._selection = Selection(item=DRAW_RECT)
        self._symbol = Rect(Pos(0, 0), Pos(1, 1))

    # TEXT ENTRY

    def on_key_press(self, widget, event):

        # TODO Will this work in other locale too?
        def filter_non_printable(ascii):
            char = ''
            if (ascii > 31 and ascii < 255) or ascii == 9:
                char = chr(ascii)
            return char

        # modifier = event.state
        # name = Gdk.keyval_name(event.keyval)
        value = event.keyval

        # check the event modifiers (can also use CONTROL_MASK, etc)
        # shift = (event.state & Gdk.ModifierType.SHIFT_MASK)
        if value == Gdk.KEY_Left or value == Gdk.KEY_BackSpace:
            if len(self._text) > 0:
                self._text = self._text[:-1]

        elif value & 255 == 13:  # enter
            self._text += '\n'

        else:
            str = filter_non_printable(value)
            self._text += str

        return True

    # DRAWING

    def do_drawing(self, ctx):
        self.draw_background(ctx)
        self.draw_gridlines(ctx)
        self.draw_content(ctx)
        self.draw_selection(ctx)

    def draw_border(self, ctx, w, h):
        """draw a border at 1% of the page-size."""
        ctx.save()

        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.25)

        ctx.rectangle(w*0.01, h*0.01, w*0.99, h*0.99)  # noqa E226
        ctx.stroke()

        ctx.restore()

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
            # no reference to surface dimension, to allow to be run from (nose) test (w/o GUI)
            # if y >= self.surface.get_height():
            #     break

    def draw_selection(self, ctx):

        ctx.save()

        if self._selection.state == IDLE:

            if self._selection.item == RECT:
                self.mark_all_objects(ctx)

        elif self._selection.state == SELECTING:
            self.draw_selecting_state(ctx)

        elif self._selection.state == SELECTED:
            self.draw_selected_state(ctx)

        ctx.restore()

    def draw_selected_state(self, ctx):
        if self._selection.item in (CHARACTER, COMPONENT):
            self._symbol.draw(ctx, self._hover_pos)

        elif self._selection.item == RECT:
            # draw the selection rectangle
            self._selection.startpos = self._drag_startpos
            self._selection.endpos = self._drag_endpos
            self._selection.draw(ctx)
            self.mark_all_objects(ctx)

        elif self._selection.item == OBJECTS:
            self.mark_all_objects(ctx)
            self.draw_selected_objects(ctx)

    def draw_selecting_state(self, ctx):
        if self._selection.item == OBJECTS:
            self.mark_all_objects(ctx)
            self.draw_cursor(ctx)

        elif self._selection.item in (TEXT, TEXT_BLOCK):
            self.draw_cursor(ctx)
            self._symbol.startpos = self._hover_pos.grid_cr()
            self._symbol.text = self._text
            self._symbol.draw(ctx)

        else:
            ctx.set_font_size(Preferences.values['FONTSIZE'])
            ctx.set_source_rgb(0.5, 0.5, 0.75)
            ctx.set_line_width(0.5)
            ctx.set_tolerance(0.1)
            ctx.set_line_join(cairo.LINE_JOIN_ROUND)

            if self._selection.item in (ROW, COL):
                self._selection.startpos = self._hover_pos
            else:
                self._selection.startpos = self._drag_startpos
            self._selection.endpos = self._drag_currentpos
            self._selection.maxpos = self.max_pos_grid

            if self._selection.item == RECT:
                self.mark_all_objects(ctx)
                self._selection.draw(ctx)

            elif self._selection.item in (MAG_LINE, LINE, DIR_LINE, DRAW_RECT):
                self._symbol.startpos = self._selection.startpos.grid_cr()
                self._symbol.endpos = self._selection.endpos.grid_cr()
                self._symbol.draw(ctx)

            elif self._selection.item:
                # draw it, if we have any valid (not None) selection
                self._selection.draw(ctx)

    def draw_cursor(self, ctx):

        ctx.save()

        ctx.set_line_width(1.5)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        if self._cursor_on:
            ctx.set_source_rgb(0.75, 0.75, 0.75)
        else:
            ctx.set_source_rgb(0.5, 0.5, 0.5)

        x, y = self._hover_pos.xy  # TODO meelopen met de tekst (blijft nu aan 't begin staan)

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

    def mark_all_objects(self, ctx):
        """Mark all objects on the grid canvas."""

        ctx.save()

        for ref in self._objects:

            if ref.symbol.has_pickpoint:

                if (self._show_symbol_pickpoints and ref.symbol.name in ('Symbol', 'Eraser')) or \
                        (self._show_line_pickpoints and ref.symbol.name in ('DirLine', 'Line', 'MagLine', 'MagLineOld', 'Rect')) or \
                        (self._show_text_pickpoints and ref.symbol.name == 'Text'):
                    ctx.set_source_rgb(1, 0, 0)
                    ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

                    pos = ref.symbol.pickpoint_pos.view_xy()

                    # the text glyph origin is its left-bottom corner
                    y_xbase = pos.y + Preferences.values['FONTSIZE']
                    ctx.move_to(pos.x, y_xbase)
                    ctx.show_text(MARK_CHAR)  # mark the upper-left corner

        ctx.restore()

    def draw_selected_objects(self, ctx):
        """Draw multiple objects selection."""

        ctx.save()

        for ref in self._objects:

            ctx.set_source_rgb(1, 0, 0)
            ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

            # offset between the current position and the ul position of the original selection rectangle
            offset = self._hover_pos - ref.startpos.view_xy()

            pos = ref.symbol.startpos.view_xy() + offset
            ref.symbol.draw(ctx, pos)

        ctx.restore()

    def on_button_press(self, widget, event):

        pos = self.calc_position(event.x, event.y)
        pub.sendMessage('POINTER_MOVED', pos=pos.grid_cr())

        if not Preferences.values['SELECTION_DRAG'] \
                and self._selection.item in (DRAW_RECT, RECT, LINE, MAG_LINE, DIR_LINE):

            if self._selection.state == IDLE:
                self.on_drag_begin(None, event.x, event.y)

            elif self._selection.state == SELECTING:
                offset = Pos(event.x, event.y) - self._drag_startpos
                self.on_drag_end(None, offset.x, offset.y)

        elif self._selection.state == SELECTING:
            self.selecting_state(pos, event)

        elif self._selection.state == SELECTED:
            self.selected_state(event)

        widget.queue_resize()

    def selected_state(self, event):

        pos = self._hover_pos
        pos = pos.grid_cr()

        if self._selection.item in (CHARACTER, COMPONENT, OBJECTS):
            # https://stackoverflow.com/questions/6616270/right-click-menu-context-menu-using-pygtk
            button = event.button
            if button == 1:
                # left button
                pub.sendMessage('PASTE_OBJECTS', pos=pos)
            elif button == 3:
                # right button
                pub.sendMessage('ROTATE_SYMBOL')

    def selecting_state(self, pos, event):

        if self._selection.item == ROW:
            row = pos.grid_cr().y
            pub.sendMessage('GRID_ROW', row=row, action=self._selection.action)

        elif self._selection.item == COL:
            col = pos.grid_cr().x
            pub.sendMessage('GRID_COL', col=col, action=self._selection.action)

        elif self._selection.item in (TEXT, TEXT_BLOCK):
            button = event.button
            if button == 1:
                # left button
                self._selection.state = SELECTED
                self._symbol.startpos = pos.grid_cr()
                pub.sendMessage('PASTE_TEXT', symbol=self._symbol)
            elif button == 3:
                # right button
                self._symbol.rotate()
                # FIXME more elegant options? otoh grid_view() is owner of the Text Symbol
                pub.sendMessage('ORIENTATION_CHANGED', ori=self._symbol.ori_as_str)

        elif self._selection.item == OBJECTS:

            # select the object within the cursor rect
            self._selection = SelectionRect()
            self._selection.state = SELECTED

            ul = pos
            br = ul + Pos(Preferences.values['GRIDSIZE_W'], Preferences.values['GRIDSIZE_H'])

            self._drag_startpos = ul
            self._drag_endpos = br

            self._selection.startpos = ul
            self._selection.endpos = br

            self._selection.maxpos = self.max_pos_grid
            self._selection.direction = HORIZONTAL

            pub.sendMessage('SELECTION_CHANGED', selected=True)

    def calc_position(self, x, y):
        """Calculate the grid view position."""
        pos = Pos(x, y)
        pos.snap_to_grid()
        return pos

    def on_drag_begin(self, widget, x_start, y_start):

        if self._selection.state == IDLE and self._selection.item in (DRAW_RECT, RECT, LINE, MAG_LINE, DIR_LINE):
            pass
        else:
            return

        pos = self.calc_position(x_start, y_start)

        self._drag_dir = None
        self._drag_startpos = pos
        self._drag_currentpos = pos

        self._drag_prevpos = []
        self._drag_prevpos.append(pos)

        self._selection.state = SELECTING

    def on_drag_end(self, widget, x_offset, y_offset):

        if self._selection.state == SELECTING and self._selection.item in (DRAW_RECT, RECT, LINE, MAG_LINE, DIR_LINE):
            pass
        else:
            return

        offset = self.calc_position(x_offset, y_offset)
        self._drag_endpos = self._drag_startpos + offset

        # position to grid (col, row) coordinates
        startpos = self._drag_startpos.grid_cr()
        endpos = self._drag_endpos.grid_cr()

        self._selection.state = SELECTED

        if self._selection.item == DRAW_RECT:
            pub.sendMessage('PASTE_RECT', startpos=startpos, endpos=endpos)

        elif self._selection.item == RECT:
            pub.sendMessage('SELECTION_CHANGED', selected=True)

        elif self._selection.item == LINE:
            if self._drag_dir == HORIZONTAL:
                endpos.y = startpos.y
            elif self._drag_dir == VERTICAL:
                endpos.x = startpos.x
            pub.sendMessage("PASTE_LINE", startpos=startpos, endpos=endpos, type=self._symbol.type)

        elif self._selection.item == MAG_LINE:
            pub.sendMessage("PASTE_MAG_LINE", startpos=startpos, endpos=endpos)

        elif self._selection.item == DIR_LINE:
            pub.sendMessage("PASTE_DIR_LINE", startpos=startpos, endpos=endpos)

    def on_drag_update(self, widget, x_offset, y_offset):

        if self._selection.state == SELECTING and self._selection.item in (DRAW_RECT, RECT, LINE, MAG_LINE, DIR_LINE):
            pass
        else:
            return

        offset = self.calc_position(x_offset, y_offset)

        pos = self._drag_startpos + offset
        pos.snap_to_grid()

        if self._selection.item in (DRAW_RECT, RECT, DIR_LINE, MAG_LINE):
            self._drag_currentpos = pos

        elif self._selection.item == LINE:
            self._drag_currentpos = pos
            # snap to either a horizontal or a vertical straight line
            self._drag_dir = self.pointer_dir()

    def pointer_dir(self):
        """Return the pointer direction in relation to the start position."""
        dx = abs(self._drag_currentpos.x - self._drag_startpos.x)
        dy = abs(self._drag_currentpos.y - self._drag_startpos.y)
        if dx > dy:
            dir = HORIZONTAL
        else:
            dir = VERTICAL
        return dir

    def pointer_dir_avg(self):
        """Return the pointer direction in relation to the previous position."""
        (x, y) = self._drag_currentpos.xy

        length = len(self._drag_prevpos)
        assert length > 0

        x_sum = 0
        y_sum = 0
        for pos in self._drag_prevpos:
            x_sum += pos.x
            y_sum += pos.y
        x_avg = x_sum / length
        y_avg = y_sum / length

        dx = abs(x - x_avg)
        dy = abs(y - y_avg)
        if dx > dy:
            dir = HORIZONTAL
        else:
            dir = VERTICAL

        # previous position keeps a list of the last n pointer locations
        self._drag_prevpos.append(Pos(x, y))
        if len(self._drag_prevpos) > 5:
            self._drag_prevpos.pop(0)
        return dir

    def on_hover(self, widget, event):
        self._hover_pos = self.calc_position(event.x, event.y)
        pub.sendMessage('POINTER_MOVED', pos=self._hover_pos.grid_cr())

        if self._selection.state == SELECTING and \
                self._selection.item == OBJECTS:
            pub.sendMessage('SELECTOR_MOVED', pos=self._hover_pos.grid_cr())

        if not Preferences.values['SELECTION_DRAG'] \
                and self._selection.state == SELECTING \
                and self._selection.item in (DRAW_RECT, RECT, LINE, MAG_LINE, DIR_LINE):
            offset = Pos(event.x, event.y) - self._drag_startpos
            self.on_drag_update(None, offset.x, offset.y)

        widget.queue_resize()
