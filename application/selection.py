"""
AACircuit
2020-03-02 JvO
"""

from application import INSERT
from application import HORIZONTAL, VERTICAL
from application.preferences import Preferences
from application import IDLE, SELECTING, SELECTED, DRAG
from application import OBJECT, TEXT, TEXT_BLOCK, COL, ROW, RECT, ERASER
from application.pos import Pos


class Selection(object):
    """
    A selection on the grid (canvas).
    All positions are canvas (x,y) coordinates.
    """

    SELECTION_STATE = (IDLE, DRAG, SELECTING, SELECTED)

    def __init__(self, item, state=IDLE):
        self._startpos = None
        self._endpos = None
        self._maxpos = None
        self._state = state
        self._item = item

    @property
    def item(self):
        return self._item

    @property
    def state(self):
        return self._state

    @state.setter
    def state(self, value):
        self._state = value

    def state_next(self):
        self._state += 1
        self._state %= len(self.SELECTION_STATE)

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
        return self._maxpos

    @maxpos.setter
    def maxpos(self, value):
        self._maxpos = value

    def draw(self, ctx):
        raise NotImplementedError


class SelectionRect(Selection):

    def __init__(self, item=RECT, state=IDLE):
        super(SelectionRect, self).__init__(item=item, state=state)

    def set_position(self, ctx):
        x_start, y_start = self._startpos.xy
        x_end, y_end = self.endpos_capped.xy
        w = x_end - x_start
        h = y_end - y_start
        ctx.rectangle(x_start, y_start, w, h)

    def draw(self, ctx):
        self.set_position(ctx)
        ctx.stroke()


class SelectionArrow(Selection):

    def __init__(self, item=RECT, state=IDLE):
        super(SelectionArrow, self).__init__(item=item, state=state)

    def _direction(self):
        dx = abs(self._endpos.x - self._startpos.x)
        dy = abs(self._endpos.y - self._startpos.y)
        if dx > dy:
            return HORIZONTAL
        else:
            return VERTICAL

    def set_position(self, ctx):
        if self._direction() == HORIZONTAL:
            poly = self.set_pos_hor()
        else:
            poly = self.set_pos_vert()
        self.draw_polyline(ctx, poly)

    def set_pos_vert(self):
        startpos = self._startpos
        endpos = self._endpos
        w = endpos.x - startpos.x
        if w == 0:
            w = 3
        w = w + w % 3
        w2 = w / 2
        w3 = w / 3
        mx = (startpos.x + endpos.x) / 2
        poly = []
        poly.append(Pos(endpos.x - w3, startpos.y))  # a
        poly.append(Pos(startpos.x + w3, startpos.y))  # b
        poly.append(Pos(startpos.x + w3, endpos.y + w2))  # c
        poly.append(Pos(startpos.x, endpos.y + w2))  # d
        poly.append(Pos(mx, endpos.y))  # e
        poly.append(Pos(endpos.x, endpos.y + w2))  # f
        poly.append(Pos(endpos.x - w3, endpos.y + w2))  # g
        poly.append(Pos(endpos.x - w3, startpos.y))  # a
        return poly

    def set_pos_hor(self):
        startpos = self._startpos
        endpos = self._endpos
        h = startpos.y - endpos.y
        if h == 0:
            h = 3
        h = h + h % 3
        h2 = h / 2
        h3 = h / 3
        my = (startpos.y + endpos.y) / 2
        poly = []
        poly.append(Pos(startpos.x, startpos.y - h3))  # a
        poly.append(Pos(startpos.x, endpos.y + h3))  # b
        poly.append(Pos(endpos.x - h2, endpos.y + h3))  # c
        poly.append(Pos(endpos.x - h2, endpos.y))  # d
        poly.append(Pos(endpos.x, my))  # e
        poly.append(Pos(endpos.x - h2, startpos.y))  # f
        poly.append(Pos(endpos.x - h2, startpos.y - h3))  # g
        poly.append(Pos(startpos.x, startpos.y - h3))  # a
        return poly

    def draw_polyline(self, ctx, poly):
        ctx.new_path()
        cmd = ctx.move_to
        for p in poly:
            p.snap_to_grid()
            cmd(p.x, p.y)
            cmd = ctx.line_to

    def draw(self, ctx):
        self.set_position(ctx)
        ctx.stroke()


class SelectionEraser(SelectionRect):

    def __init__(self, item=ERASER):
        super(SelectionEraser, self).__init__(item=item)

    def draw(self, ctx):
        self.set_position(ctx)
        ctx.set_source_rgba(0.75, 0.75, 0.75, 0.5)
        ctx.fill()


class SelectionObject(SelectionRect):

    def __init__(self, item=OBJECT, state=SELECTING):
        super(SelectionObject, self).__init__(item=item, state=state)


class SelectionCol(Selection):

    def __init__(self, action, state=SELECTING):
        super(SelectionCol, self).__init__(item=COL, state=state)
        self._action = action

    @property
    def action(self):
        return self._action

    def draw(self, ctx):
        """
        Highlight the selected column.  Green or red color when inserting respectively deleting a column.
        """
        if self._action == INSERT:
            ctx.set_source_rgb(0, 1, 0)
        else:
            ctx.set_source_rgb(1, 0, 0)
        x = self._startpos.x
        if x <= self._maxpos.x:
            ctx.new_path()
            ctx.move_to(x, 0)
            ctx.line_to(x, self._maxpos.y)
            ctx.move_to(x + Preferences.values['GRIDSIZE_W'], 0)
            ctx.line_to(x + Preferences.values['GRIDSIZE_W'], self._maxpos.y)
            ctx.stroke()


class SelectionRow(Selection):

    def __init__(self, action, state=SELECTING):
        super(SelectionRow, self).__init__(item=ROW, state=state)
        self._action = action

    @property
    def action(self):
        return self._action

    def draw(self, ctx):
        """
        Highlight the selected row. Green or red color when inserting respectively deleting a row.
        """
        if self._action == INSERT:
            ctx.set_source_rgb(0, 1, 0)
        else:
            ctx.set_source_rgb(1, 0, 0)
        y = self._startpos.y
        if y <= self._maxpos.y:
            ctx.new_path()
            ctx.move_to(0, y)
            ctx.line_to(self._maxpos.x, y)
            ctx.move_to(0, y + Preferences.values['GRIDSIZE_H'])
            ctx.line_to(self._maxpos.x, y + Preferences.values['GRIDSIZE_H'])
            ctx.stroke()


class SelectionText(Selection):

    def __init__(self, text="", item=TEXT, state=SELECTING):
        super(SelectionText, self).__init__(item=item, state=state)
        self._text = text

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    def draw(self, ctx):
        y = self._startpos.y
        str = self._text.split('\n')
        for line in str:
            x = self._startpos.x
            for char in line:
                x += Preferences.values['GRIDSIZE_W']
                ctx.move_to(x, y)
                ctx.show_text(char)
            y += Preferences.values['GRIDSIZE_H']  # TODO check max?


class SelectionTextBlock(SelectionText):

    def __init__(self, text=""):
        super(SelectionTextBlock, self).__init__(text=text, item=TEXT_BLOCK)
