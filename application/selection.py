"""
AACircuit
2020-03-02 JvO
"""

from numpy import sign
# from bresenham import bresenham

from application import GRIDSIZE_W, GRIDSIZE_H
from application import HORIZONTAL, VERTICAL
from application import LINE_HOR, LINE_VERT, TERMINAL_TYPE
from application.pos import Pos


class Selection(object):
    """A selection on the grid (canvas)."""

    def __init__(self):
        self._startpos = None
        self._endpos = None
        self._maxpos = None

    @property
    def startpos(self):
        return self._startpos

    @startpos.setter
    def startpos(self, value):
        self._startpos = value

    @property
    def endpos(self):
        return self._endpos

    @endpos.setter
    def endpos(self, value):
        self._endpos = value

    @property
    def endpos_capped(self):
        """Return end position capped by the coordinates maximum."""
        x, y = self._endpos.xy
        if self._endpos.x > self._maxpos.x:
            x = self._maxpos.x
        if self._endpos.y > self._maxpos.y:
            y = self._maxpos.y
        return Pos(x, y)

    @property
    def maxpos(self):
        return self.maxpos

    @maxpos.setter
    def maxpos(self, value):
        self._maxpos = value

    def draw(self, ctx):
        raise NotImplementedError


class SelectionLine(Selection):

    def __init__(self, type):
        super(SelectionLine, self).__init__()

        self._dir = None
        if type is None:
            self._line_terminal = None
        else:
            self._line_terminal = TERMINAL_TYPE[type]

    @property
    def direction(self):
        return self._dir

    @direction.setter
    def direction(self, value):
        self._dir = value

    def draw(self, ctx):
        if self._dir == HORIZONTAL:
            self.draw_hor(ctx, self._startpos, self._endpos)
        elif self._dir == VERTICAL:
            self.draw_vert(ctx, self._startpos, self._endpos)

    def draw_hor(self, ctx, startpos, endpos):

        if self._line_terminal is None:
            linechar = LINE_HOR
        else:
            linechar = self._line_terminal

        x_start = startpos.x
        x_end = endpos.x + GRIDSIZE_W
        y = startpos.y + GRIDSIZE_H

        step = GRIDSIZE_W * sign(x_end - x_start)
        if step < 0:
            x_end = endpos.x

        if abs(step) > 0:
            for x in range(x_start, x_end, step):
                ctx.move_to(x, y)
                ctx.show_text(linechar)
                linechar = LINE_HOR

    def draw_vert(self, ctx, startpos, endpos):

        if self._line_terminal is None:
            linechar = LINE_HOR
        else:
            linechar = self._line_terminal

        y_start = startpos.y + GRIDSIZE_H
        y_end = endpos.y
        x = startpos.x

        step = GRIDSIZE_H * sign(y_end - y_start)
        if step > 0:
            y_end = endpos.y + 2 * GRIDSIZE_H
        if abs(step) > 0:
            for y in range(y_start, y_end, step):
                ctx.move_to(x, y)
                ctx.show_text(linechar)
                linechar = LINE_VERT


class SelectionMagicLine(SelectionLine):

    def __init__(self):
        super(SelectionMagicLine, self).__init__(type=None)

        self._ml_dir = None

        self._ml_startpos = None
        self._ml_endpos = None
        self._ml_maxpos = None

    @property
    def ml_direction(self):
        return self._ml_dir

    @ml_direction.setter
    def ml_direction(self, value):
        self._ml_dir = value

    @property
    def ml_startpos(self):
        return self._ml_startpos

    @ml_startpos.setter
    def ml_startpos(self, value):
        self._ml_startpos = value

    @property
    def ml_endpos(self):
        return self._ml_endpos

    @ml_endpos.setter
    def ml_endpos(self, value):
        self._ml_endpos = value

    @property
    def ml_endpos_capped(self):
        """Return magic line endposition capped by the coordinates maximum."""
        x, y = self._ml_endpos.xy
        if self._ml_endpos.x > self._maxpos.x:
            x = self._maxpos.x
        if self._ml_endpos.y > self._maxpos.y:
            y = self._maxpos.y
        return Pos(x, y)

    def draw(self, ctx):

        if self._dir == HORIZONTAL:
            self.draw_hor(ctx, self._startpos, self._endpos)
        elif self._dir == VERTICAL:
            self.draw_vert(ctx, self._startpos, self._endpos)

        if self._ml_dir is not None:
            # draw magic line
            x_start, y_start = self._ml_startpos.xy
            x_end, y_end = self._ml_endpos.xy

            x_end += GRIDSIZE_W
            y_end += GRIDSIZE_H
            y_start += GRIDSIZE_H

            if self._ml_dir == HORIZONTAL:
                self.draw_hor(ctx, self._ml_startpos, self._ml_endpos)
            elif self._ml_dir == VERTICAL:
                self.draw_vert(ctx, self._ml_startpos, self._ml_endpos)


class SelectionLineFree(Selection):

    def __init__(self):
        super(SelectionLineFree, self).__init__()

    def draw(self, ctx):
        # linechar = "/"  # TODO
        # line = bresenham(self._x_start, self._y_start, self._x_end, self._y_end)
        # for pos in line:
        #     ctx.move_to(pos[0], pos[1])
        #     ctx.show_text(linechar)

        x_start, y_start = self._startpos.xy
        x_end, y_end = self._endpos_capped.xy

        ctx.move_to(x_start, y_start)
        ctx.line_to(x_end, y_end)
        ctx.stroke()


class SelectionRect(Selection):

    def __init__(self):
        super(SelectionRect, self).__init__()

    def draw(self, ctx):
        ctx.new_path()

        x_start, y_start = self._startpos.xy
        x_end, y_end = self._endpos_capped.xy

        # w, h = (self._endpos - self._startpos).xy
        w = x_end - x_start
        h = y_end - y_start
        ctx.rectangle(x_start, y_start, w, h)
        ctx.stroke()


class SelectionCol(Selection):

    def __init__(self):
        super(SelectionCol, self).__init__()

    def draw(self, ctx):
        # highlight the selected column
        x = self._startpos.x
        ctx.new_path()
        ctx.move_to(x, 0)
        ctx.line_to(x, self._maxpos.y)
        ctx.move_to(x + GRIDSIZE_W, 0)
        ctx.line_to(x + GRIDSIZE_W, self._maxpos.y)
        ctx.stroke()


class SelectionRow(Selection):

    def __init__(self):
        super(SelectionRow, self).__init__()

    def draw(self, ctx):
        # highlight the selected row
        y = self._startpos.y
        ctx.new_path()
        ctx.move_to(0, y)
        ctx.line_to(self._maxpos.x, y)
        ctx.move_to(0, y + GRIDSIZE_H)
        ctx.line_to(self._maxpos.x, y + GRIDSIZE_H)
        ctx.stroke()


class SelectionText(Selection):

    def __init__(self):
        super(SelectionText, self).__init__()

        self._text = "?"

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    def draw(self, ctx):
        x, y = self._startpos.xy
        str = self._text.split('\n')
        for line in str:
            ctx.move_to(x, y)
            ctx.show_text(line)
            y += GRIDSIZE_H  # TODO check max?
