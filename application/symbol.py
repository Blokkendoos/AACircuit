'''
AACircuit
2020-03-02 JvO
'''

import copy
import json

from application import _
from application.pos import Pos
from application import HORIZONTAL, VERTICAL
from application import LINE_HOR, LINE_VERT, TERMINAL_TYPE
from application import COMPONENT, CHARACTER, TEXT, DRAW_RECT, LINE
from application.symbol_view import ComponentView, ObjectView


class Symbol(object):

    ORIENTATION = {0: "N", 1: "E", 2: "S", 3: "W"}

    def __init__(self, id=0, dict=None, ori=None, mirrored=None, startpos=None, form=None):

        self._id = id

        if ori is None:
            self._ori = 0
        else:
            self._ori = ori

        if mirrored is None:
            self._mirrored = 0
        else:
            self._mirrored = mirrored

        if dict is None:
            self._grid = self.default
        else:
            self._grid = dict

        if startpos is None:
            self._startpos = Pos(0, 0)
        else:
            self._startpos = startpos

        if form is None:
            self._form = {}
        else:
            self._form = form

    def __str__(self):
        str = _("symbol id: {0} orientation: {1}").format(self._id, self.ORIENTATION[self._ori])
        return str

    @property
    def view(self):
        return ComponentView(self.grid, self._startpos)

    @property
    def id(self):
        return self._id

    @property
    def ori(self):
        return self._ori

    @ori.setter
    def ori(self, value):
        # orientation can be set as the grid is dynamically selected (in grid() method)
        if value in (0, 1, 2, 3):
            self._ori = value

    @property
    def mirrored(self):
        # mirrored can only be set via the mirror() method
        return self._mirrored

    @property
    def form(self):
        return self._form

    @property
    def startpos(self):
        return self._startpos

    @startpos.setter
    def startpos(self, value):
        self._startpos = value

    @property
    def default(self):
        # default provides one ("N" orientation) grid only
        grid = {'N': [
            ' ___ ',
            '|__ \\',
            '  / /',
            ' |_| ',
            ' (_) ']}
        return grid

    def memo(self):
        """Return entry for the actions as recorded in the memo."""
        str = "{0}:{1},{2},{3},{4}".format(COMPONENT, self._id, self._ori, self._mirrored, self._startpos)
        return str

    def copy(self):
        ori = copy.deepcopy(self._ori)
        mirrored = copy.deepcopy(self._mirrored)
        grid = copy.deepcopy(self._grid)
        startpos = copy.deepcopy(self._startpos)
        form = copy.deepcopy(self._form)
        return Symbol(self._id, grid, ori, mirrored, startpos, form)

    @property
    def grid(self):
        return self._grid[self.ORIENTATION[self._ori]]

    def grid_next(self):
        """Return the grid with the next (90° clockwise rotated) orientation for this symbol."""
        self._ori += 1
        self._ori %= 4
        return self._grid[self.ORIENTATION[self._ori]]

    def paste(self, pos, grid):
        """Paste symbol into the target grid.

        :param pos: the (col,row) coordinate of the upper left position of the symbol grid in the target grid
        :param grid: the target grid
        """
        grid.fill_rect(pos, self.grid)

    def mirror(self):
        """Return the grid vertically mirrored."""
        if self._grid is None:
            return
            # return [[]]

        # mirror specific characters
        switcher = {'/': '\\',
                    '\\': '/',
                    '<': '>',
                    '>': '<',
                    '(': ')',
                    ')': '('
                    }
        grid = []

        for r, row in enumerate(self._grid[self.ORIENTATION[self._ori]]):
            rev = []
            for c in reversed(row):
                try:
                    rev.append(switcher[c])
                except KeyError:
                    rev.append(c)
            grid.append(rev)

        self._grid[self.ORIENTATION[self._ori]] = grid

        self._mirrored += 1
        self._mirrored %= 2


class Character(Symbol):

    def __init__(self, char):

        id = ord(char)
        grid = {"N": [[char]]}
        super(Character, self).__init__(id=id, dict=grid)

    @property
    def grid(self):
        return self._grid[self.ORIENTATION[0]]

    def memo(self):
        str = "{0}:{1},{2}".format(CHARACTER, self._id, self._startpos)
        return str

    def grid_next(self):
        # print("Not implemented")
        return


class Text(Symbol):

    def __init__(self, pos, text):

        grid = {"N": [['?']]}
        super(Text, self).__init__(startpos=pos, dict=grid)

        self._text = text
        self._representation(self._startpos)

    @property
    def grid(self):
        return self._grid[self.ORIENTATION[0]]

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    @property
    def view(self):
        return ObjectView(self._form, self._startpos)

    def memo(self):
        jstext = json.dumps(self._text)
        str = "{0}:{1},{2}".format(TEXT, self._startpos, jstext)
        return str

    def _representation(self, pos):

        self._form = {}

        startpos = pos
        incr = Pos(1, 0)
        for line in self._text:
            for char in line:
                # startpoint terminal
                if char == '\n':
                    pos.x = startpos.x
                    pos += Pos(-1, 1)  # skip the cr, go to next line
                self._form[pos] = char
                pos += incr

    def grid_next(self):
        # print("Not implemented")
        return

    def paste(self, pos, grid):
        y = pos.y
        str = self._text.split('\n')
        for line in str:
            x = pos.x
            for char in line:
                x += 1
                targetpos = Pos(x, y)
                grid.set_cell(targetpos, char)
            y += 1  # TODO check boundary?


class Line(Symbol):

    def __init__(self, startpos, endpos, type=0):
        super(Line, self).__init__(id=type, startpos=startpos)

        self._endpos = endpos
        self._type = type
        self._terminal = TERMINAL_TYPE[type]

        self._direction()
        self._line(self._startpos)

    def _direction(self):
        if self._startpos.x == self._endpos.x:
            self._dir = VERTICAL
        elif self._startpos.y == self._endpos.y:
            self._dir = HORIZONTAL
        else:
            self._dir = None

    def grid_next(self):
        # TODO enable to rotate (from HOR to VERT)?
        print("Not implemented")

    def memo(self):
        str = "{0}:{1},{2},{3}".format(LINE, self._type, self._startpos, self._endpos)
        return str

    @property
    def view(self):
        return ObjectView(self._form, self._startpos)

    def _line(self, pos):
        """
        Compose the line elements

        :param pos: the (col,row) coordinate of the upper left position of this line in the target grid
        :param grid: the target grid
        """

        self._form = {}
        start = self._startpos
        end = self._endpos

        offset = pos - start
        end += offset

        # print("start:", start, " end:", end)

        if self._dir == HORIZONTAL:
            line_char = LINE_HOR
            incr = Pos(1, 0)
        elif self._dir == VERTICAL:
            line_char = LINE_VERT
            incr = Pos(0, 1)
        else:
            line_char = "?"
            incr = Pos(1, 1)

        if self._terminal is None:
            terminal = line_char
        else:
            terminal = self._terminal

        # startpoint terminal
        self._form[pos] = terminal
        pos += incr

        # TODO make this one string (and support an appropriate fill method for this in grid)
        while pos < end:
            self._form[pos] = line_char
            pos += incr

        # endpoint terminal
        self._form[pos] = terminal

    def paste(self, pos, grid):

        self._line(pos)

        for key, value in self._form.items():
            grid.set_cell(key, value)


class Rect(Symbol):

    def __init__(self, startpos, endpos):
        super(Rect, self).__init__(startpos=startpos)

        self._endpos = endpos

        self._rect()

    def _rect(self):

        ul = self._startpos
        ur = Pos(self._endpos.x, self._startpos.y)
        bl = Pos(self._startpos.x, self._endpos.y)
        br = self._endpos

        # print("ul:", ul, " ur:", ur, "\nbl:", bl, "br:", br)

        type = '3'

        line1 = Line(ul, ur, type)
        line2 = Line(ur, br, type)
        line3 = Line(bl, br, type)
        line4 = Line(ul, bl, type)

        form = {}
        form.update(line1._form)
        form.update(line2._form)
        form.update(line3._form)
        form.update(line4._form)
        self._form = form

    def grid_next(self):

        w = self._endpos.x - self._startpos.x
        h = self._endpos.y - self._startpos.y

        ul = self._startpos
        br = Pos(self._startpos.x + h, self._startpos.y + w)

        self._startpos = ul
        self._endpos = br
        self._rect()

    @property
    def view(self):
        return ObjectView(self._form, self._startpos)

    def memo(self):
        str = "{0}:{1},{2}".format(DRAW_RECT, self._startpos, self._endpos)
        return str

    def paste(self, pos, grid):

        start = self._startpos
        end = self._endpos

        offset = pos - start
        start = pos
        end += offset

        ul = start
        ur = Pos(end.x, start.y)
        bl = Pos(start.x, end.y)
        br = end

        # print("ul:", ul, " ur:", ur, "\nbl:", bl, "br:", br)

        type = '3'

        line1 = Line(ul, ur, type)
        line2 = Line(ur, br, type)
        line3 = Line(bl, br, type)
        line4 = Line(ul, bl, type)

        line1.paste(ul, grid)
        line2.paste(ur, grid)
        line3.paste(bl, grid)
        line4.paste(ul, grid)
