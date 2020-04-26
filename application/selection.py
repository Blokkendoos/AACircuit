"""
AACircuit
2020-03-02 JvO
"""

from application import GRIDSIZE_W, GRIDSIZE_H
from application import IDLE, SELECTING, SELECTED, DRAG
from application import TEXT, TEXT_BLOCK, COL, ROW, RECT
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

    def __init__(self, item=RECT):
        super(SelectionRect, self).__init__(item=item)

    def draw(self, ctx):
        x_start, y_start = self._startpos.xy
        x_end, y_end = self.endpos_capped.xy

        # w, h = (self._endpos - self._startpos).xy
        w = x_end - x_start
        h = y_end - y_start
        ctx.rectangle(x_start, y_start, w, h)
        ctx.stroke()


class SelectionCol(Selection):

    def __init__(self, action):
        super(SelectionCol, self).__init__(item=COL)

        self._action = action
        self._state = SELECTING

    @property
    def action(self):
        return self._action

    def draw(self, ctx):
        # highlight the selected column
        x = self._startpos.x
        if x <= self._maxpos.x:
            ctx.new_path()
            ctx.move_to(x, 0)
            ctx.line_to(x, self._maxpos.y)
            ctx.move_to(x + GRIDSIZE_W, 0)
            ctx.line_to(x + GRIDSIZE_W, self._maxpos.y)
            ctx.stroke()


class SelectionRow(Selection):

    def __init__(self, action):
        super(SelectionRow, self).__init__(item=ROW)

        self._action = action
        self._state = SELECTING

    @property
    def action(self):
        return self._action

    def draw(self, ctx):
        # highlight the selected row
        y = self._startpos.y
        if y <= self._maxpos.y:
            ctx.new_path()
            ctx.move_to(0, y)
            ctx.line_to(self._maxpos.x, y)
            ctx.move_to(0, y + GRIDSIZE_H)
            ctx.line_to(self._maxpos.x, y + GRIDSIZE_H)
            ctx.stroke()


class SelectionText(Selection):

    def __init__(self, text="", item=TEXT):
        super(SelectionText, self).__init__(item=item)

        self._state = SELECTING
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
                x += GRIDSIZE_W
                ctx.move_to(x, y)
                ctx.show_text(char)
            y += GRIDSIZE_H  # TODO check max?


class SelectionTextBlock(SelectionText):

    def __init__(self, text=""):
        super(SelectionTextBlock, self).__init__(text=text, item=TEXT_BLOCK)
