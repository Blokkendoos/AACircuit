"""
AACircuit
2020-03-02 JvO
"""

import cairo
import time
from pubsub import pub

# https://pypi.org/project/profilehooks/
# from profilehooks import coverage
# from profilehooks import timecall

from application import _
from application import FONTSIZE, GRIDSIZE_W, GRIDSIZE_H
from application import HORIZONTAL, VERTICAL
from application import IDLE, SELECTING, SELECTED
from application import CHARACTER, COMPONENT, LINE, MAG_LINE, DIR_LINE, OBJECTS, COL, ROW, RECT, DRAW_RECT
from application import MARK_CHAR
from application import TEXT, TEXT_BLOCK
from application.pos import Pos
from application.selection import Selection, SelectionLine, SelectionCol, SelectionRow, SelectionRect
from application.symbol import Symbol, Character, Text, Line, MagLine, DirLine, Rect, Row, Column

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GLib  # noqa: E402


class GridView(Gtk.Frame):

    def __init__(self):

        super(GridView, self).__init__()

        self.set_border_width(0)

        self.surface = None
        self._grid = None
        self._objects = None
        self._hover_pos = Pos(0, 0)

        # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html
        self._drawing_area = Gtk.DrawingArea()
        self.add(self._drawing_area)

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

        self._drawing_area.set_can_focus(True)

        self._drawing_area.connect('draw', self.on_draw)
        self._drawing_area.connect('configure-event', self.on_configure)

        # https://www.programcreek.com/python/example/84675/gi.repository.Gtk.DrawingArea
        self._drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self._drawing_area.connect('button-press-event', self.on_button_press)

        # https://stackoverflow.com/questions/44098084/how-do-i-handle-keyboard-events-in-gtk3
        self._drawing_area.add_events(Gdk.EventMask.KEY_PRESS_MASK)
        self._drawing_area.connect('key-press-event', self.on_key_press)

        self._gesture_drag = Gtk.GestureDrag.new(self._drawing_area)
        self._gesture_drag.connect('drag-begin', self.on_drag_begin)
        self._gesture_drag.connect('drag-end', self.on_drag_end)
        self._gesture_drag.connect('drag-update', self.on_drag_update)

        self._drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self._drawing_area.connect('motion-notify-event', self.on_hover)

        # https://developer.gnome.org/gtk3/stable/GtkWidget.html#gtk-widget-add-tick-callback
        self.start_time = time.time()
        self.cursor_callback = self._drawing_area.add_tick_callback(self.toggle_cursor)
        # self._drawing_area.remove_tick_callback(self.cursor_callback)

        # subscriptions

        pub.subscribe(self.set_grid, 'GRID')

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

    def set_grid(self, grid):
        self._grid = grid
        self.set_viewport_size()
        self.queue_draw()

    def set_viewport_size(self):
        # https://stackoverflow.com/questions/11546395/how-to-put-gtk-drawingarea-into-gtk-layout
        width = self._grid.nr_cols * GRIDSIZE_W
        height = self._grid.nr_rows * GRIDSIZE_H
        self.set_size_request(width, height)

    def init_surface(self, area):
        """Initialize Cairo surface."""
        if self.surface is not None:
            # destroy previous buffer
            self.surface.finish()
            self.surface = None

        # create a new buffer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())

    @property
    def max_pos(self):
        x_max = self.surface.get_width()
        y_max = self.surface.get_height()
        return Pos(x_max, y_max)

    @property
    def max_pos_grid(self):
        x_max = self._grid.nr_cols * GRIDSIZE_W
        y_max = self._grid.nr_rows * GRIDSIZE_H
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

        ul = ul.grid_rc()
        br = br.grid_rc()

        return ul, br

    def on_configure(self, area, event, data=None):
        self.init_surface(self._drawing_area)
        context = cairo.Context(self.surface)
        self.do_drawing(context)
        self.surface.flush()
        return False

    def on_draw(self, area, context):
        if self.surface is not None:
            context.set_source_surface(self.surface, 0.0, 0.0)
            context.paint()
        else:
            print(_("Invalid surface"))
        return False

    # printing

    # def on_begin_print(self, operation, print_ctx, print_data):
    def on_begin_print(self, parms):
        operation, print_ctx = parms

        operation.set_n_pages(1)

    # def on_draw_page(self, operation, print_ctx, page_num, print_data):
    def on_draw_page(self, parms):
        operation, print_ctx, page_num = parms

        ctx = print_ctx.get_cairo_context()
        w = print_ctx.get_width()
        h = print_ctx.get_height()

        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.25)

        ctx.rectangle(w*0.1, h*0.1, w*0.8, h*0.8)  # noqa E226
        ctx.stroke()

        ctx.scale(0.5, 0.5)
        self.draw_content(ctx)

        # msg = "Finished..."
        # pub.sendMessage('STATUS_MESSAGE', msg=msg)

    # drawing

    def do_drawing(self, ctx):
        self.draw_background(ctx)
        self.draw_gridlines(ctx)
        self.draw_content(ctx)
        self.draw_selection(ctx)
        self.queue_draw()

    def gridsize_changed(self, *args, **kwargs):
        self.set_viewport_size()

    # SELECTIONs

    def on_nothing_selected(self):
        self._selection = Selection(None)
        self.queue_resize()

    def on_add_text(self):
        self._selection = Selection(item=TEXT, state=SELECTING)
        self._text = ""
        self._drawing_area.grab_focus()

    def on_add_textblock(self, text):
        self._selection = Selection(item=TEXT_BLOCK, state=SELECTING)
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

    def on_draw_dir_line(self, type):
        self._selection = Selection(item=DIR_LINE)

    def on_draw_line(self, type):
        self._selection = SelectionLine(item=LINE, type=type)

    def on_draw_rect(self):
        self._selection = Selection(item=DRAW_RECT)

    # TEXT ENTRY

    def on_key_press(self, widget, event):

        # TODO Will this work in other locale too?
        def filter_non_printable(ascii):
            char = ''
            if (ascii > 31 and ascii < 255) or ascii == 9:
                char = chr(ascii)
            return char

        # TODO Only for TEXT necessary
        # if self._selection.item == TEXT:

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
        x_incr = GRIDSIZE_W
        y_incr = GRIDSIZE_H

        # horizontal lines
        y = GRIDSIZE_H
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

        ctx.set_font_size(FONTSIZE)
        ctx.set_source_rgb(0.1, 0.1, 0.1)
        ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        y = GRIDSIZE_H
        for r in self._grid.grid:
            x = 0
            for c in r:
                ctx.move_to(x, y)
                ctx.show_text(str(c))
                x += GRIDSIZE_W

            y += GRIDSIZE_H
            if y >= self.surface.get_height():
                break

    # @coverage
    # @timecall
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

        elif self._selection.item in (TEXT, TEXT_BLOCK):
            self.draw_cursor(ctx)
            if self._selection.item == TEXT:
                self._selection.text = self._text
            self._selection.startpos = self._hover_pos
            self._selection.draw(ctx)

        else:
            ctx.set_font_size(FONTSIZE)
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
            self._selection.direction = self._drag_dir

            if self._selection.item == RECT:
                self.mark_all_objects(ctx)

            elif self._selection.item == MAG_LINE:
                symbol = MagLine(self._selection.startpos.grid_rc(), self._selection.endpos.grid_rc(), self._grid.cell)
                symbol.draw(ctx)
            elif self._selection.item == DRAW_RECT:
                symbol = Rect(self._selection.startpos.grid_rc(), self._selection.endpos.grid_rc())
                symbol.draw(ctx)
            else:
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

        x, y = (self._hover_pos + Pos(0, -GRIDSIZE_H)).xy  # TODO meelopen met de tekst (blijft nu aan 't begin staan)

        ctx.rectangle(x, y, GRIDSIZE_W, GRIDSIZE_H)
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

    def mark_all_objects(self, ctx):
        """Mark all objects on the grid canvas."""

        ctx.save()

        for ref in self._objects:

            ctx.set_source_rgb(1, 0, 0)
            ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

            pos = ref.startpos.view_xy()

            ctx.move_to(pos.x, pos.y)
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

        pos = Pos(event.x, event.y)
        pos.snap_to_grid()
        pub.sendMessage('POINTER_MOVED', pos=pos.grid_rc())

        if self._selection.state == SELECTING:
            self.selecting_state(pos)

        elif self._selection.state == SELECTED:
            self.selected_state(event)

        widget.queue_resize()

    def selected_state(self, event):

        pos = self._hover_pos + Pos(0, -1)
        pos = pos.grid_rc()

        if self._selection.item == CHARACTER:
            button = event.button
            if button == 1:
                pub.sendMessage('PASTE_CHARACTER', pos=pos)

        elif self._selection.item == COMPONENT:
            # https://stackoverflow.com/questions/6616270/right-click-menu-context-menu-using-pygtk
            button = event.button
            if button == 1:
                # left button
                pub.sendMessage('PASTE_SYMBOL', pos=pos)
            elif button == 3:
                # right button
                pub.sendMessage('ROTATE_SYMBOL')

        elif self._selection.item == OBJECTS:
            button = event.button
            if button == 1:
                pub.sendMessage('PASTE_OBJECTS', pos=pos)

    def selecting_state(self, pos):

        if self._selection.item == ROW:
            row = pos.grid_rc().y
            pub.sendMessage('GRID_ROW', row=row, action=self._selection.action)
            self.gridsize_changed()

        elif self._selection.item == COL:
            col = pos.grid_rc().x
            pub.sendMessage('GRID_COL', col=col, action=self._selection.action)
            self.gridsize_changed()

        elif self._selection.item == TEXT:
            self._selection.state = SELECTED
            pub.sendMessage('PASTE_TEXT', pos=pos.grid_rc(), text=self._text)

        elif self._selection.item == TEXT_BLOCK:
            self._selection.state = SELECTED
            pub.sendMessage('PASTE_TEXTBLOCK', pos=pos.grid_rc(), text=self._selection.text)

        elif self._selection.item == OBJECTS:

            # FIXME this is a hack (switching from one to another Selection subclass)

            # and select the object within this rect
            self._selection = SelectionRect()
            self._selection.state = SELECTED

            # create a small rect (one cell in all directions)
            ul = pos - Pos(GRIDSIZE_W, GRIDSIZE_H)
            br = pos + Pos(2 * GRIDSIZE_W, GRIDSIZE_H)

            self._drag_startpos = ul
            self._drag_endpos = br

            self._selection.startpos = ul
            self._selection.endpos = br

            self._selection.maxpos = self.max_pos_grid
            self._selection.direction = HORIZONTAL

            pub.sendMessage('SELECTION_CHANGED', selected=True)

    def on_drag_begin(self, widget, x_start, y_start):

        if self._selection.state == IDLE and self._selection.item in (DRAW_RECT, RECT, LINE, MAG_LINE, DIR_LINE):
            None
        else:
            return

        pos = Pos(x_start, y_start)
        pos.snap_to_grid()

        self._drag_dir = None
        self._drag_startpos = pos
        self._drag_currentpos = pos

        self._drag_prevpos = []
        self._drag_prevpos.append(pos)

        self._selection.state = SELECTING

    def on_drag_end(self, widget, x_offset, y_offset):

        if self._selection.state == SELECTING and self._selection.item in (DRAW_RECT, RECT, LINE, MAG_LINE, DIR_LINE):
            None
        else:
            return

        offset = Pos(x_offset, y_offset)
        self._drag_endpos = self._drag_startpos + offset
        self._drag_endpos.snap_to_grid()

        # position to grid (col, row) coordinates
        startpos = self._drag_startpos.grid_rc()
        endpos = self._drag_endpos.grid_rc()

        self._selection.state = SELECTED

        if self._selection.item == DRAW_RECT:

            # TODO move this to the Symbol class?
            if startpos > endpos:
                tmp = endpos
                endpos = startpos
                startpos = tmp

            pub.sendMessage('PASTE_RECT', startpos=startpos, endpos=endpos)

        elif self._selection.item == RECT:
            pub.sendMessage('SELECTION_CHANGED', selected=True)

        elif self._selection.item == LINE:

            if self._drag_dir == HORIZONTAL:
                endpos.y = startpos.y
            elif self._drag_dir == VERTICAL:
                endpos.x = startpos.x
            pub.sendMessage("PASTE_LINE", startpos=startpos, endpos=endpos, type=self._selection.type)

        elif self._selection.item == MAG_LINE:
            pub.sendMessage("PASTE_MAG_LINE", startpos=startpos, endpos=endpos)

        elif self._selection.item == DIR_LINE:
            pub.sendMessage("PASTE_DIR_LINE", startpos=startpos, endpos=endpos)

    def on_drag_update(self, widget, x_offset, y_offset):

        if self._selection.state == SELECTING and self._selection.item in (DRAW_RECT, RECT, LINE, MAG_LINE, DIR_LINE):
            None
        else:
            return

        offset = Pos(x_offset, y_offset)
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
        self._hover_pos = Pos(event.x, event.y)
        self._hover_pos.snap_to_grid()
        pub.sendMessage('POINTER_MOVED', pos=self._hover_pos.grid_rc())

        widget.queue_resize()
