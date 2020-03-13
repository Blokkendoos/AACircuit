"""
AACircuit
2020-03-02 JvO
"""

import cairo

# import gi
# gi.require_version('Gtk', '3.0')
# from gi.repository import Gtk, Gdk  # noqa: E402


class SymbolCanvas(object):

    SIZE = 30
    FONTSIZE = 12
    GRIDSIZE_W = 7
    GRIDSIZE_H = 16

    # https://athenajc.gitbooks.io/python-gtk-3-api/content/gtk-group/gtkdrawingarea.html

    def __init__(self, grid=None):
        self._grid = grid

    @property
    def grid(self):
        return self._grid

    @grid.setter
    def grid(self, grid):
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

        x_start, y = pos

        # snap to grid
        x_start -= x_start % self.GRIDSIZE_W
        y -= y % self.GRIDSIZE_H

        for r in self._grid:
            x = x_start
            for c in r:
                ctx.move_to(x, y)
                ctx.show_text(str(c))
                x += self.GRIDSIZE_W
                if x >= surface.get_width():
                    break

            y += self.GRIDSIZE_H
            if y >= surface.get_height():
                break

        self._pos = None

        # ctx.restore()
