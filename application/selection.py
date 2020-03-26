"""
AACircuit
2020-03-02 JvO
"""

from numpy import sign
from bresenham import bresenham

from application import TERMINAL1, TERMINAL2, TERMINAL3, TERMINAL4
from application import GRIDSIZE_W, GRIDSIZE_H
from application import HORIZONTAL, VERTICAL
from application import LINE_HOR, LINE_VERT


class Selection(object):
    """A selection on the grid (canvas)."""

    def __init__(self):

        self._startpos = None
        self._endpos = None
        self._maxpos = None

        self._x_start = None
        self._y_start = None

        self._x_end = None
        self._y_end = None

        self._x_max = None
        self._y_max = None

    @property
    def startpos(self):
        return self._startpos

    @startpos.setter
    def startpos(self, value):
        self._startpos = value
        self._x_start = value.x
        self._y_start = value.y

    @property
    def endpos(self):
        return self._endpos

    @endpos.setter
    def endpos(self, value):
        self._endpos = value
        self._x_end = value.x
        self._y_end = value.y

    @property
    def x_end(self):
        """Return capped endposition x coordinate."""
        if self._x_end > self._x_max:
            return self._x_max
        else:
            return self._x_end

    @property
    def y_end(self):
        """Return capped endposition y coordinate."""
        if self._y_end > self._y_max:
            return self._y_max
        else:
            return self._y_end

    @property
    def maxpos(self):
        return self.maxpos

    @maxpos.setter
    def maxpos(self, value):
        self._maxpos = value
        self._x_max = value.x
        self._y_max = value.y

    def draw(self, ctx):
        raise NotImplementedError


class SelectionLine(Selection):

    def __init__(self, type):

        super(SelectionLine, self).__init__()
        self._dir = None

        if type == '1':
            self._line_terminal = TERMINAL1
        elif type == '2':
            self._line_terminal = TERMINAL2
        elif type == '3':
            self._line_terminal = TERMINAL3
        elif type == '4':
            self._line_terminal = TERMINAL4
        else:
            self._line_terminal = None

    @property
    def direction(self):
        return self._dir

    @direction.setter
    def direction(self, value):
        self._dir = value

    def draw(self, ctx):
        if self._dir == HORIZONTAL:
            self.draw_hor(ctx)
        elif self._dir == VERTICAL:
            self.draw_vert(ctx)

    def draw_hor(self, ctx):

        if self._line_terminal is None:
            linechar = LINE_HOR
        else:
            linechar = self._line_terminal

        x_start = self._x_start
        x_end = self._x_end + GRIDSIZE_W
        y = self._y_start + GRIDSIZE_H

        step = GRIDSIZE_W * sign(x_end - x_start)
        if step < 0:
            x_end = self._x_end

        if abs(step) > 0:
            for x in range(x_start, x_end, step):
                ctx.move_to(x, y)
                ctx.show_text(linechar)
                linechar = LINE_HOR

    def draw_vert(self, ctx):

        if self._line_terminal is None:
            linechar = LINE_HOR
        else:
            linechar = self._line_terminal

        y_start = self._y_start + GRIDSIZE_H
        y_end = self._y_end
        x = self._x_start

        step = GRIDSIZE_H * sign(y_end - y_start)
        if step > 0:
            y_end = self._y_end + 2 * GRIDSIZE_H
        if abs(step) > 0:
            for y in range(y_start, y_end, step):
                ctx.move_to(x, y)
                ctx.show_text(linechar)
                linechar = LINE_VERT


class SelectionMagicLine(SelectionLine):

    def __init__(self):
        super(SelectionMagicLine, self).__init__(type=None)


class SelectionLineFree(Selection):

    def __init__(self):
        super(SelectionLineFree, self).__init__()

    def draw(self, ctx):
        # linechar = "/"  # TODO
        # line = bresenham(self._x_start, self._y_start, self._x_end, self._y_end)
        # for pos in line:
        #     ctx.move_to(pos[0], pos[1])
        #     ctx.show_text(linechar)
        ctx.move_to(self._x_start, self._y_start)
        ctx.line_to(self.x_end, self.y_end)
        ctx.stroke()


class SelectionRect(Selection):

    def __init__(self):
        super(SelectionRect, self).__init__()

    def draw(self, ctx):
        ctx.new_path()
        x = self._x_start
        y = self._y_start
        # w, h = (self._endpos - self._startpos).xy
        w = self.x_end - self._startpos.x
        h = self.y_end - self._startpos.y
        ctx.rectangle(x, y, w, h)
        ctx.stroke()


class SelectionCol(Selection):

    def __init__(self):
        super(SelectionCol, self).__init__()

    def draw(self, ctx):
        # highlight the selected column
        x = self._x_start
        ctx.new_path()
        ctx.move_to(x, 0)
        ctx.line_to(x, self._y_max)
        ctx.move_to(x + GRIDSIZE_W, 0)
        ctx.line_to(x + GRIDSIZE_W, self._y_max)
        ctx.stroke()


class SelectionRow(Selection):

    def __init__(self):
        super(SelectionRow, self).__init__()

    def draw(self, ctx):
        # highlight the selected row
        y = self._y_start
        ctx.new_path()
        ctx.move_to(0, y)
        ctx.line_to(self._x_max, y)
        ctx.move_to(0, y + GRIDSIZE_H)
        ctx.line_to(self._x_max, y + GRIDSIZE_H)
        ctx.stroke()
