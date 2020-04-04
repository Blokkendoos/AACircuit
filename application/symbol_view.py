"""
AACircuit
2020-03-02 JvO
"""

from application import GRIDSIZE_W, GRIDSIZE_H
from pubsub import pub
import cairo


class SymbolView(object):
    """"Draw a single selected symbol."""

    def __init__(self, grid=None, form={}, startpos=None):

        self._grid = grid
        self._form = form
        self._startpos = startpos

        pub.subscribe(self.set_grid, 'SYMBOL_SELECTED')
        pub.subscribe(self.set_grid, 'CHARACTER_SELECTED')

    def set_grid(self, symbol):
        """
        The symbol 'sprite'.

        :param grid: a 2D array of ASCII chars
        """
        self._grid = symbol.grid

    def draw(self, ctx, pos):
        """
        Draw the symbol on the canvas.

        :param ctx: Cairo context
        :param pos: the canvas (x,y) coordinate

        """
        ctx.set_source_rgb(1, 0, 0)
        ctx.select_font_face('monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        if len(self._form) > 0:
            self._draw_object(ctx, pos)
        else:
            # symbol is represented by a 'sprite'
            self._draw_symbol(ctx, pos)

    def _draw_object(self, ctx, pos):
        for char_pos, char in self._form.items():
            # the position relative to the pointer, in view (x,y) coordinates
            relative_pos = pos + (char_pos - self._startpos).view_xy()
            x, y = relative_pos.xy
            ctx.move_to(x, y)
            ctx.show_text(str(char))

    def _draw_symbol(self, ctx, pos):

        surface = ctx.get_target()

        x_start, y = pos.xy
        for row in self._grid:
            x = x_start
            for char in row:
                ctx.move_to(x, y)
                ctx.show_text(str(char))
                x += GRIDSIZE_W
                if x >= surface.get_width():
                    break

            y += GRIDSIZE_H
            if y >= surface.get_height():
                break
