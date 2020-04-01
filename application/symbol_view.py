"""
AACircuit
2020-03-02 JvO
"""

from application import GRIDSIZE_W, GRIDSIZE_H
from pubsub import pub
import cairo


class SymbolView(object):
    """"Draw a single selected symbol."""

    def __init__(self, grid=None):

        self._grid = grid

        pub.subscribe(self.set_grid, 'SYMBOL_SELECTED')
        pub.subscribe(self.set_grid, 'CHARACTER_SELECTED')

    def set_grid(self, symbol):
        """
        The symbol grid.
        :param grid: a 2D array of ASCII chars
        """
        self._grid = symbol.grid()

    def draw(self, ctx, pos):
        """
        Draw the symbol grid.

        :param ctx: Cairo context
        :param pos: the canvas (x,y) coordinate

        """
        if self._grid is None or pos is None:
            return

        surface = ctx.get_target()

        ctx.set_source_rgb(1, 0, 0)
        ctx.select_font_face('monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

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
