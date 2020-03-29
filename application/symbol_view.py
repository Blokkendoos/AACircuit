"""
AACircuit
2020-03-02 JvO
"""

from application import GRIDSIZE_W, GRIDSIZE_H
from pubsub import pub
import cairo


class SymbolView(object):

    # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html

    def __init__(self):

        self._grid = None

        pub.subscribe(self.set_grid, 'SYMBOL_SELECTED')
        pub.subscribe(self.set_grid, 'CHARACTER_SELECTED')

    def set_grid(self, symbol):
        """
        The symbol grid.
        :param grid: a 2D array of ASCII chars
        """
        self._grid = symbol.grid()

    def draw(self, ctx, pos):

        if self._grid is None or pos is None:
            return

        surface = ctx.get_target()

        ctx.set_source_rgb(1, 0, 0)
        ctx.select_font_face('monospace', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

        x_start, y = pos.x, pos.y
        for r in self._grid:
            x = x_start
            for c in r:
                ctx.move_to(x, y)
                ctx.show_text(str(c))
                x += GRIDSIZE_W
                if x >= surface.get_width():
                    break

            y += GRIDSIZE_H
            if y >= surface.get_height():
                break
