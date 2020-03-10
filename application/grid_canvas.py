"""
AACircuit
2020-03-02 JvO
"""

import cairo

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf  # noqa: E402

SIZE = 30
FONTSIZE = 12
GRIDSIZE_W = 7
GRIDSIZE_H = 16


class GridCanvas(Gtk.Frame):
    # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html

    def __init__(self, grid=None):

        super().__init__()

        self.set_border_width(0)

        # https://stackoverflow.com/questions/11546395/how-to-put-gtk-drawingarea-into-gtk-layout
        self.set_size_request(700, 700)

        self.surface = None

        overlay = Gtk.Overlay()
        self.add(overlay)

        self.drawing_area = Gtk.DrawingArea()
        overlay.add_overlay(self.drawing_area)

        self._grid = grid

        self.set_symbol()
        self._pos = None

        # connect signals

        self.drawing_area.connect("draw", self.on_draw)
        self.drawing_area.connect('configure-event', self.on_configure)

        # https://www.programcreek.com/python/example/84675/gi.repository.Gtk.DrawingArea
        self.drawing_area.add_events(Gdk.EventMask.BUTTON_PRESS_MASK)
        self.drawing_area.connect('button_press_event', self.on_button_press)

        self.drawing_area.add_events(Gdk.EventMask.POINTER_MOTION_MASK)
        self.drawing_area.connect('motion-notify-event', self.on_hover)

    @property
    def grid(self):
        return self._grid

    @grid.setter
    def grid(self, grid):
        self._grid = grid

    def set_symbol(self):
        self.symbol = [
            [" ", "|", " "],
            [".", "+", "."],
            ["|", " ", "|"],
            ["|", " ", "|"],
            [".", "+", "."],
            [" ", "|", " "]]

    def init_surface(self, area):
        """Initialize Cairo surface"""
        # destroy previous buffer
        if self.surface is not None:
            self.surface.finish()
            self.surface = None

        # create a new buffer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())

    def redraw(self):
        """if we receive a draw event redraw our grid"""
        self.init_surface(self.drawing_area)
        context = cairo.Context(self.surface)
        # context.scale(self.surface.get_width(), self.surface.get_height())
        # context.scale(self.surface.get_width() / 4, self.surface.get_height() / 4)
        # w = self.surface.get_width()
        # h = self.surface.get_height()
        # print("Context w:{0} h:{1}".format(w, h))
        self.do_drawing(context)
        self.draw_symbol()
        self.surface.flush()

    def on_configure(self, area, event, data=None):
        self.redraw()
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

    def draw_lines(self, ctx):

        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        x_max = self.surface.get_width()
        x_incr = GRIDSIZE_W

        y_max = self.surface.get_height()
        y_incr = GRIDSIZE_H

        ctx.save()

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

        ctx.restore()

    def draw_content(self, ctx):

        if self._grid is None:
            return

        ctx.set_source_rgb(0.1, 0.1, 0.1)
        # ctx.set_line_width(0.5)
        # ctx.set_tolerance(0.1)
        # ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        ctx.save()

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

        ctx.restore()


    def draw_symbol(self):

        if self.symbol is None or self._pos is None:
            return

        ctx = cairo.Context(self.surface)
        ctx.set_source_rgb(0.1, 0.1, 0.5)
        # ctx.set_line_width(0.5)
        # ctx.set_tolerance(0.1)
        # ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        ctx.save()

        x_start, y = self._pos
        for r in self.symbol:
            x = x_start
            for c in r:
                ctx.move_to(x, y)
                ctx.show_text(str(c))
                x += GRIDSIZE_W
                if x >= self.surface.get_width():
                    break

            y += GRIDSIZE_H
            if y >= self.surface.get_height():
                break

        ctx.restore()

    def on_button_press(self, widget, event):
        print(event.x, ' ', event.y)
        self._pos = (event.x, event.y)
        # self.draw_symbol(pos)

    def on_hover(self, widget, event):
        # print(event.x, ' ', event.y)
        # self._pos = (event.x, event.y)
        #self.draw_symbol(pos)
