"""
AACircuit
2020-03-02 JvO
"""

import cairo

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, GdkPixbuf  # noqa: E402

SIZE = 30


class GridCanvas(Gtk.Frame):
    # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html

    def __init__(self, grid=None):

        super().__init__()

        self.set_border_width(0)

        # https://stackoverflow.com/questions/11546395/how-to-put-gtk-drawingarea-into-gtk-layout
        self.set_size_request(700, 700)

        self.surface = None

        self.area = Gtk.DrawingArea()
        self.add(self.area)

        self._grid = grid

        # connect signals

        self.area.connect("draw", self.on_draw)
        self.area.connect('configure-event', self.on_configure)

    @property
    def grid(self):
        return self._grid

    @grid.setter
    def grid(self, grid):
        self._grid = grid

    def init_surface(self, area):
        # destroy previous buffer
        if self.surface is not None:
            self.surface.finish()
            self.surface = None

        # create a new buffer
        self.surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, area.get_allocated_width(), area.get_allocated_height())
        w = area.get_allocated_width()

    def redraw(self):
        """if we receive a draw event redraw our grid"""
        self.init_surface(self.area)
        context = cairo.Context(self.surface)
        # context.scale(self.surface.get_width(), self.surface.get_height())
        # context.scale(self.surface.get_width() / 4, self.surface.get_height() / 4)
        # w = self.surface.get_width()
        # h = self.surface.get_height()
        # print("Context w:{0} h:{1}".format(w, h))
        self.do_drawing(context)
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
        # self.draw_radial_gradient_rect(ctx)

    def draw_radial_gradient_rect(self, ctx):
        x0, y0 = 0.3, 0.3
        x1, y1 = 0.5, 0.5
        r0 = 0
        r1 = 1
        pattern = cairo.RadialGradient(x0, y0, r0, x1, y1, r1)
        pattern.add_color_stop_rgba(0, 1, 1, 0.5, 1)
        pattern.add_color_stop_rgba(1, 0.2, 0.4, 0.1, 1)
        ctx.rectangle(0, 0, 1, 1)
        ctx.set_source(pattern)
        ctx.fill()

    def draw_lines(self, ctx):

        ctx.set_source_rgb(0.75, 0.75, 0.75)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        ctx.save()

        x = self.surface.get_width()
        y = self.surface.get_height()

        # horizontal lines
        for y in range(0, y, 10):
            ctx.new_path()
            ctx.move_to(0, y)
            ctx.line_to(x, y)
            ctx.stroke()

        # vertical lines
        for x in range(0, x, 10):
            ctx.new_path()
            ctx.move_to(x, 0)
            ctx.line_to(x, y)
            ctx.stroke()

        ctx.restore()

    def draw_content(self, ctx):

        if self._grid is None:
            return

        ctx.set_source_rgb(0.5, 0.5, 0.5)
        ctx.set_line_width(0.5)
        ctx.set_tolerance(0.1)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)

        ctx.select_font_face("Courier", cairo.FONT_SLANT_NORMAL,
                            cairo.FONT_WEIGHT_NORMAL)
        ctx.set_font_size(13)

        ctx.save()

        x = 0
        y = 0
        for r in self._grid.grid:
            ctx.new_path()
            ctx.move_to(x, y)
            # txt = cairo.text_path(ctx, str(r))
            ctx.show_text(str(r))
            ctx.stroke()

            y += 13
            if y >= self.surface.get_height():
                break

        ctx.restore()
