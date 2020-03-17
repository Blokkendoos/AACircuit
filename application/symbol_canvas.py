"""
AACircuit
2020-03-02 JvO
"""

from application import GRIDSIZE_W, GRIDSIZE_H
# from application.grid_canvas import Pos
from pubsub import pub
import cairo


class SymbolCanvas(object):

    # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html

    def __init__(self):
        self._grid = None

        # subscriptions

        pub.subscribe(self.set_grid, 'SYMBOL_SELECTED')

    def set_grid(self, grid):
        """
        The symbol grid.
        :param grid: a 2D array of ASCII chars
        """
        if grid is None:
            # default grid (Resistor)
            self._grid = [
                [" ", "|", " "],
                [".", "+", "."],
                ["|", " ", "|"],
                ["|", " ", "|"],
                [".", "+", "."],
                [" ", "|", " "]]
        else:
            self._grid = grid

    def draw(self, ctx, pos):

        if self._grid is None or pos is None:
            return

        # ctx.save()

        surface = ctx.get_target()

        ctx.set_source_rgb(1, 0, 0)
        ctx.select_font_face("monospace", cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)

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

        self._pos = None

        # ctx.restore()
