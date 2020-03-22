"""
AACircuit
2020-03-02 JvO
"""

import cairo
from pubsub import pub
from numpy import sign

from application import GRIDSIZE_W, GRIDSIZE_H
from application import INSERT, REMOVE, HORIZONTAL, VERTICAL
from application import IDLE, SELECTING, SELECTED
from application import COMPONENT, COL, ROW, RECT, LINE, MAG_LINE
from application import LINE_HOR, LINE_VERT, TERMINAL1, TERMINAL2, TERMINAL3, TERMINAL4
from application.symbol_view import SymbolView

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402


class Pos(object):
    """A position on the grid (canvas)."""

    def __init__(self, x, y):
        self._x = int(x)
        self._y = int(y)

    def __add__(self, other):
        x = self._x + other.x
        y = self._y + other.y
        return Pos(x, y)

    def __sub__(self, other):
        x = self._x - other.x
        y = self._y - other.y
        return Pos(x, y)

    def __str__(self):
        return "x:{0} y:{1}".format(self._x, self._y)

    @property
    def x(self):
        return self._x

    @property
    def y(self):
        return self._y

    @property
    def xy(self):
        return (self._x, self._y)

    def snap_to_grid(self):
        """Set position to the nearest (canvas) grid coordinate."""
        (x, y) = (self._x, self._y)
        x -= x % GRIDSIZE_W
        y -= y % GRIDSIZE_H
        self._x = int(x)
        self._y = int(y)

    def grid_rc(self):
        """Map canvas (x,y) position to grid (col,row) coordinates."""
        (x, y) = (self._x, self._y)
        x /= GRIDSIZE_W
        y /= GRIDSIZE_H
        return Pos(x, y)


class GridView(Gtk.Frame):

    # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html

    def __init__(self):

        super().__init__()

        self.set_border_width(0)

        # https://stackoverflow.com/questions/11546395/how-to-put-gtk-drawingarea-into-gtk-layout
        self.set_size_request(640, 480)

        self.surface = None
        self._grid = None
        self._pos = None

        self._drawing_area = Gtk.DrawingArea()
        self.add(self._drawing_area)

        self._symbol_view = SymbolView()

        # selection status
        self._selection_state = IDLE
        self._selection_action = None
        self._selection = None
        self._selection_type = None
        self._selection_mag_line_split = None

        # selection rectangle
        self._drag_startpos = None
        self._drag_endpos = None
        self._drag_currentpos = None
        self._drag_prevpos = []
        self._drag_prevcnt = 0

        self._drawing_area.connect("draw", self.on_draw)
        self._drawing_area.connect('configure-event', self.on_configure)

        # https://www.programcreek.com/python/example/84675/gi.repository.Gtk.DrawingArea
        self._drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self._drawing_area.connect('button_press_event', self.on_button_press)

        self._gesture_drag = Gtk.GestureDrag.new(self._drawing_area)
        self._gesture_drag.connect('drag-begin', self.on_drag_begin)
        self._gesture_drag.connect('drag-end', self.on_drag_end)
        self._gesture_drag.connect('drag-update', self.on_drag_update)

        self._drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self._drawing_area.connect('motion-notify-event', self.on_hover)

        # subscriptions

        pub.subscribe(self.set_grid, 'GRID')
        pub.subscribe(self.on_symbol_selected, 'SYMBOL_SELECTED')
        pub.subscribe(self.on_select_rect, 'SELECT_RECT')
        pub.subscribe(self.on_selecting_row, 'SELECTING_ROW')
        pub.subscribe(self.on_selecting_col, 'SELECTING_COL')
        pub.subscribe(self.on_nothing_selected, 'NOTHING_SELECTED')

        pub.subscribe(self.on_draw_mag_line, 'DRAW_MAG_LINE')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE1')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE2')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE3')
        pub.subscribe(self.on_draw_line, 'DRAW_LINE4')
        pub.subscribe(self.on_draw_line, 'DRAW_RECT')  # TODO on_draw_rect

    def set_grid(self, grid):
        self._grid = grid
        self._drawing_area.queue_resize()

    def init_surface(self, area):
        """Initialize Cairo surface."""
        # destroy previous buffer
        if self.surface is not None:
            self.surface.finish()
            self.surface = None

        # create a new buffer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())

    @property
    def max_pos(self):
        x_max = self.surface.get_width()
        y_max = self.surface.get_height()
        return x_max, y_max

    @property
    def max_pos_grid(self):
        x_max = self._grid.nr_cols * GRIDSIZE_W
        y_max = self._grid.nr_rows * GRIDSIZE_H
        return x_max, y_max

    @property
    def drag_rect(self):
        """Return the upper-left position and width and height of the selected rectangle."""
        if self._drag_startpos.x <= self._drag_endpos.x:
            x1 = self._drag_startpos.x
            x2 = self._drag_endpos.x
        else:
            x1 = self._drag_endpos.x
            x2 = self._drag_startpos.x

        if self._drag_startpos.y <= self._drag_endpos.y:
            y1 = self._drag_startpos.y
            y2 = self._drag_endpos.y
        else:
            y1 = self._drag_endpos.y
            y2 = self._drag_startpos.y

        # TODO handle negative width/height in grid
        # x1, y1 = self._drag_startpos.xy
        # x2, y2 = self._drag_endpos.xy

        pos = Pos(x1, y1).grid_rc()
        # width and height in grid (col,row) dimensions
        w = int((x2 - x1) / GRIDSIZE_W)
        h = int((y2 - y1) / GRIDSIZE_H)

        return pos, w, h

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
            print('Invalid surface')
        return False

    def do_drawing(self, ctx):
        """Draw the ASCII grid."""
        self.draw_background(ctx)
        self.draw_lines(ctx)
        self.draw_content(ctx)
        self.draw_selection(ctx)
        if self._selection == COMPONENT:  # and self._selection_state == SELECTED:
            self._symbol_view.draw(ctx, self._pos)

    def on_nothing_selected(self):
        self._selection_state = IDLE
        self._selection_action = None
        self._selection = None
        self._drawing_area.queue_resize()

    def on_symbol_selected(self, symbol):
        self._selection_state = SELECTED
        self._selection_action = INSERT
        self._selection = COMPONENT

    def on_select_rect(self, action):
        self._selection_state = IDLE
        self._selection_action = action
        self._selection = RECT

    def on_selecting_row(self, action):
        self._selection_state = SELECTING
        self._selection_action = action
        self._selection = ROW

    def on_selecting_col(self, action):
        self._selection_state = SELECTING
        self._selection_action = action
        self._selection = COL

    def on_draw_mag_line(self, type):
        self._selection_state = IDLE
        self._selection_action = None
        self._selection = MAG_LINE

    def on_draw_line(self, type):
        self._selection_state = IDLE
        self._selection_action = None
        self._selection = LINE
        self._selection_type = type
        if type == '1':
            self._line_terminal = TERMINAL1
        elif type == '2':
            self._line_terminal = TERMINAL2
        elif type == '3':
            self._line_terminal = TERMINAL3
        elif type == '4':
            self._line_terminal = TERMINAL4
        else:
            # TODO draw line https://pypi.org/project/bresenham/
            self._line_terminal = "?"

    def draw_background(self, ctx):
        """Draw a background with the size of the grid."""
        ctx.set_source_rgb(0.95, 0.95, 0.85)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max, y_max = self.max_pos_grid

        ctx.new_path()
        ctx.rectangle(0, 0, x_max, y_max)
        ctx.fill()

    def draw_lines(self, ctx):

        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max, y_max = self.max_pos
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

    def draw_selection(self, ctx):

        ctx.set_source_rgb(0.5, 0.5, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max, y_max = self.max_pos

        if self._selection_state == SELECTING:
            x, y = (self._pos.x, self._pos.y)

        if self._selection_state == SELECTING:
            if self._selection == COL:
                # highlight the selected column
                ctx.new_path()
                ctx.move_to(x, 0)
                ctx.line_to(x, y_max)
                ctx.move_to(x + GRIDSIZE_W, 0)
                ctx.line_to(x + GRIDSIZE_W, y_max)
                ctx.stroke()

            elif self._selection == ROW:
                # highlight the selected row
                ctx.new_path()
                ctx.move_to(0, y)
                ctx.line_to(x_max, y)
                ctx.move_to(0, y + GRIDSIZE_H)
                ctx.line_to(x_max, y + GRIDSIZE_H)
                ctx.stroke()

            elif self._selection == RECT:
                # draw the selection rectangle
                ctx.new_path()
                x, y = self._drag_startpos.xy
                w, h = (self._drag_currentpos - self._drag_startpos).xy
                ctx.rectangle(x, y, w, h)
                ctx.stroke()

            elif self._selection == LINE:

                # draw line
                x_start, y_start = self._drag_startpos.xy
                x_end, y_end = self._drag_currentpos.xy

                if self._selection_action == HORIZONTAL:
                    linechar = LINE_HOR
                    y = y_start + GRIDSIZE_H
                    step = GRIDSIZE_W * sign(x_end - x_start)
                    for x in range(x_start, x_end, step):
                        ctx.move_to(x, y)
                        ctx.show_text(linechar)
                        if x >= self.surface.get_width():
                            break

                elif self._selection_action == VERTICAL:
                    linechar = LINE_VERT
                    x = x_start
                    step =  GRIDSIZE_H * sign(y_end - y_start)
                    if abs(step) > 0:
                        for y in range(y_start, y_end, step):
                            ctx.move_to(x, y)
                            ctx.show_text(linechar)
                            if y >= self.surface.get_height():
                                break

        elif self._selection_state == SELECTED and self._selection == RECT:
            # draw the selection rectangle
            ctx.new_path()
            x, y = self._drag_startpos.xy
            w, h = (self._drag_endpos - self._drag_startpos).xy
            ctx.rectangle(x, y, w, h)
            ctx.stroke()

    def draw_content(self, ctx):

        if self._grid is None:
            return

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

    def on_button_press(self, widget, event):

        pos = Pos(event.x, event.y)
        pos.snap_to_grid()
        pub.sendMessage('POINTER_MOVED', pos=pos.grid_rc())

        # print("state:{0} selection:{1}".format(self._selection_state, self._selection))

        if self._selection_state == SELECTING and self._selection == ROW:
            row = pos.grid_rc().y
            if self._selection_action == INSERT:
                pub.sendMessage('INSERT_ROW', row=row)
            else:
                pub.sendMessage('REMOVE_ROW', row=row)

        elif self._selection_state == SELECTING and self._selection == COL:
            col = pos.grid_rc().x
            if self._selection_action == INSERT:
                pub.sendMessage('INSERT_COL', col=col)
            else:
                pub.sendMessage('REMOVE_COL', col=col)

        elif self._selection_state == SELECTED and self._selection == COMPONENT:
            # https://stackoverflow.com/questions/6616270/right-click-menu-context-menu-using-pygtk
            button = event.button
            if button == 1:
                # left button
                pos = self._pos + Pos(0, -1)
                pub.sendMessage('PASTE_SYMBOL', pos=pos.grid_rc())
            elif button == 3:
                # right button
                pub.sendMessage('ROTATE_SYMBOL')
            else:
                None

        widget.queue_resize()

    def on_drag_begin(self, widget, x_start, y_start):
        if self._selection_state == IDLE and self._selection in (RECT, LINE, MAG_LINE):
            pos = Pos(x_start, y_start)
            pos.snap_to_grid()
            self._drag_startpos = pos
            self._drag_currentpos = pos
            self._drag_prevpos.append(pos)

            self._selection_state = SELECTING
            self._selection_action = None

    def on_drag_end(self, widget, x_offset, y_offset):

        if self._selection_state == SELECTING and self._selection in (RECT, LINE, MAG_LINE):

            offset = Pos(x_offset, y_offset)
            self._drag_endpos = self._drag_startpos + offset
            self._drag_endpos.snap_to_grid()

            self._selection_state = SELECTED

            if self._selection == LINE:

                # pos in grid (col, row) coordinates
                pos = self._drag_startpos.grid_rc()

                # convert (canvas) length to grid dimension (nr cols or rows)
                if self._selection_action == HORIZONTAL:
                    length = int(x_offset / GRIDSIZE_W)
                    if sign(length) == -1:
                        pos = Pos(pos.x + length, pos.y)
                        pos -= Pos(1, 0)  # compensation?
                else:
                    length = int(y_offset / GRIDSIZE_H)
                    if sign(length) == -1:
                        pos = Pos(pos.x, pos.y + length)
                        pos -= Pos(0, 1)  # compensation?

                length = abs(length)

                # TODO line terminal-type
                pub.sendMessage("PASTE_LINE", pos=pos, dir=self._selection_action, type=self._selection_type, length=length)

    def on_drag_update(self, widget, x_offset, y_offset):

        if self._selection_state == SELECTING and self._selection in (RECT, LINE, MAG_LINE):

            offset = Pos(x_offset, y_offset)
            self._drag_currentpos = (self._drag_startpos + offset)
            self._drag_currentpos.snap_to_grid()

            if self._selection == LINE:
                # snap to either a horizontal or a vertical straight line
                self._selection_action = self.pointer_dir()

            if self._selection == MAG_LINE:
                self._selection_action = self.pointer_dir()
                # snap to either a horizontal or a vertical straight line
                if self._selection_action != self.pointer_dir2():
                    print("line break")

    def pointer_dir(self):
        """Return the pointer direction in relation to the start position."""
        dx = abs(self._drag_currentpos.x - self._drag_startpos.x)
        dy = abs(self._drag_currentpos.y - self._drag_startpos.y)
        if dx > dy:
            dir = HORIZONTAL
        else:
            dir = VERTICAL
        return dir

    def pointer_dir2(self):
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

        self._drag_prevpos.append(Pos(x, y))
        self._drag_prevcnt += 1
        if self._drag_prevcnt > 4:
            self._drag_prevpos.pop(0)
        return dir

    def on_hover(self, widget, event):
        self._pos = Pos(event.x, event.y)
        self._pos.snap_to_grid()
        pub.sendMessage('POINTER_MOVED', pos=self._pos.grid_rc())

        widget.queue_resize()
