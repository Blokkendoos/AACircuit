"""
AACircuit
2020-03-02 JvO
"""

import cairo
from pubsub import pub

from application import GRIDSIZE_W, GRIDSIZE_H
from application import INSERT, REMOVE
from application import IDLE, SELECTING, SELECTED, COL, ROW
from application.symbol_canvas import SymbolCanvas

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk  # noqa: E402


class GridCanvas(Gtk.Frame):

    # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html

    def __init__(self):

        super().__init__()

        self.set_border_width(0)

        # https://stackoverflow.com/questions/11546395/how-to-put-gtk-drawingarea-into-gtk-layout
        self.set_size_request(700, 700)

        self.surface = None

        overlay = Gtk.Overlay()
        self.add(overlay)

        self.drawing_area = Gtk.DrawingArea()
        overlay.add_overlay(self.drawing_area)

        self._grid = None

        self._symbol_canvas = SymbolCanvas()
        self._pos = None

        # active row/column selection
        self._selection_state = IDLE
        self._selection_action = None
        self._selection = None
        self._cr_selected = None

        # connect signals

        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.connect('configure-event', self.on_configure)

        # https://www.programcreek.com/python/example/84675/gi.repository.Gtk.DrawingArea
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area.connect('button_press_event', self.on_button_press)

        self.drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.drawing_area.connect('motion-notify-event', self.on_hover)

        # subscriptions

        pub.subscribe(self.set_grid, 'GRID')
        pub.subscribe(self.on_selecting_row, 'SELECTING_ROW')
        pub.subscribe(self.on_selecting_col, 'SELECTING_COL')

    def set_grid(self, grid):
        self._grid = grid

    def init_surface(self, area):
        """Initialize Cairo surface"""
        # destroy previous buffer
        if self.surface is not None:
            self.surface.finish()
            self.surface = None

        # create a new buffer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())

    def max_pos(self):
        x_max = self.surface.get_width()
        y_max = self.surface.get_height()
        return (x_max, y_max)

    def on_configure(self, area, event, data=None):
        self.init_surface(self.drawing_area)
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
        self.draw_lines(ctx)
        self.draw_content(ctx)
        self.draw_selection(ctx)
        self._symbol_canvas.draw(ctx, self._pos)

    def on_selecting_row(self, action):
        self._selection_state = SELECTING
        self._selection_action = action
        self._selection = ROW

    def on_selecting_col(self, action):
        self._selection_state = SELECTING
        self._selection_action = action
        self._selection = COL

    def draw_lines(self, ctx):

        # ctx.save()

        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max, y_max = self.max_pos()
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

        # ctx.restore()

    def draw_selection(self, ctx):

        ctx.set_source_rgb(0.5, 0.5, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max, y_max = self.max_pos()

        if self._selection_state == SELECTING:
            x, y = self._pos

        elif self._selection_state == SELECTED and self._selection == COL:
            x = self._cr_selected
            y = 0

        elif self._selection_state == SELECTED and self._selection == ROW:
            x = 0
            y = self._cr_selected

        if self._selection == COL and self._selection_state != IDLE:
            # highlight the selected column
            ctx.new_path()
            ctx.move_to(x, 0)
            ctx.line_to(x, y_max)
            ctx.move_to(x + GRIDSIZE_W, 0)
            ctx.line_to(x + GRIDSIZE_W, y_max)
            ctx.stroke()

        elif self._selection == ROW and self._selection_state != IDLE:
            # highlight the selected row
            ctx.new_path()
            ctx.move_to(0, y)
            ctx.line_to(x_max, y)
            ctx.move_to(0, y + GRIDSIZE_H)
            ctx.line_to(x_max, y + GRIDSIZE_H)
            ctx.stroke()

    def draw_content(self, ctx):

        if self._grid is None:
            return

        # ctx.save()

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

        # ctx.restore()

    def on_button_press(self, widget, event):

        pos = (event.x, event.y)
        self.snap_to_grid(pos)

        if self._selection_state == SELECTING and self._selection == ROW:
            self._selection_state = IDLE
            row = self.get_grid_xy()[1]
            if self._selection_action == INSERT:
                pub.sendMessage('INSERT_ROW', row=row)
            else:
                pub.sendMessage('REMOVE_ROW', row=row)

        elif self._selection_state == SELECTING and self._selection == COL:
            self._selection_state = IDLE
            col = self.get_grid_xy()[0]
            if self._selection_action == INSERT:
                pub.sendMessage('INSERT_COL', col=col)
            else:
                pub.sendMessage('REMOVE_COL', col=col)

        else:
            # https://stackoverflow.com/questions/6616270/right-click-menu-context-menu-using-pygtk
            button = event.button
            if button == 1:
                # left button
                pub.sendMessage('PASTE_SYMBOL', pos=self.get_grid_xy())
            elif button == 3:
                # right button
                pub.sendMessage('ROTATE_SYMBOL')
            else:
                None

        # widget.queue_draw()
        widget.queue_resize()


    def on_hover(self, widget, event):
        # print("col:{0} row:{1}".format(self._selecting_col, self._selecting_row))
        pos = (event.x, event.y)
        self.snap_to_grid(pos)
        widget.queue_resize()

    def snap_to_grid(self, pos):
        """Align position to (the canvas) grid."""
        (x, y) = pos
        x -= x % GRIDSIZE_W
        y -= y % GRIDSIZE_H
        self._pos = (int(x), int(y))

    def get_grid_xy(self):
        """Map the canvas position to grid coordinates."""
        (x, y) = self._pos
        x /= GRIDSIZE_W
        y /= GRIDSIZE_H
        if y > 0:
            y -= 1
        return (int(x), int(y))
