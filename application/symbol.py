'''
AACircuit
2020-03-02 JvO
'''

import copy
import json

from application import _
from application.pos import Pos
from application import INSERT, COL, ROW
from application import HORIZONTAL, VERTICAL
from application import LINE_HOR, LINE_VERT, TERMINAL_TYPE, ML_BEND_CHAR, JUMP_CHAR
from application import COMPONENT, CHARACTER, TEXT, DRAW_RECT, LINE, MAG_LINE
from application.symbol_view import ComponentView, ObjectView


class Symbol(object):
    """
    Symbol represented by a grid.

    :param id: the component id
    :param dict: the character-grid that create the symbol
    :param ori: orientation (0-3)
    :param mirrored: set to 1 to mirror the symbol vertically
    :param startpos: the upper-left corner (col,row) coordinate of the character-grid
    :param endpos: used in subclasses, e.g. Line
    """

    ORIENTATION = {0: "N", 1: "E", 2: "S", 3: "W"}

    def __init__(self, id=0, grid=None, ori=None, mirrored=None, startpos=None, endpos=None):

        self._id = id

        if ori is None:
            self._ori = 0
        else:
            self._ori = ori

        if mirrored is None:
            self._mirrored = 0
        else:
            self._mirrored = mirrored

        if grid is None:
            self._grid = self.default
        else:
            self._grid = grid

        if startpos is None:
            self._startpos = Pos(0, 0)
        else:
            self._startpos = startpos

        if endpos is None:
            self._endpos = Pos(0, 0)
        else:
            self._endpos = endpos

        self._repr = dict()

    def __str__(self):
        str = _("symbol id: {0} orientation: {1}").format(self._id, self.ORIENTATION[self._ori])
        return str

    def _representation(self):
        # raise NotImplementedError
        return

    @property
    def width(self):
        """Return the width of the symbol grid."""
        # dimensions of grid (taking into account the orientation)
        return len(self.grid[0])

    @property
    def height(self):
        """Return the heigth of the symbol grid."""
        # dimensions of grid (taking into account the orientation)
        return len(self.grid)

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
        return self._mirrored

    @mirrored.setter
    def mirrored(self, value):
        self._mirrored = value

    @property
    def repr(self):
        return self._repr

    @property
    def startpos(self):
        return self._startpos

    @startpos.setter
    def startpos(self, value):
        self._startpos = value

        # representation may be changed due to a changed start/end position
        self._representation()

    @property
    def endpos(self):
        return self._endpos

    @endpos.setter
    def endpos(self, value):
        self._endpos = value

        # representation may be changed due to a changed start/end position
        self._representation()

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
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        return Symbol(id=self._id, grid=self._grid, ori=ori, mirrored=mirrored, startpos=startpos, endpos=endpos)

    @property
    def grid(self):
        if self._mirrored == 1:
            return self.mirror(self._grid[self.ORIENTATION[self._ori]])
        else:
            return self._grid[self.ORIENTATION[self._ori]]

    def grid_next(self):
        """Return the grid with the next (90° clockwise rotated) orientation for this symbol."""
        self._ori += 1
        self._ori %= 4

        return self.grid

    def paste(self, grid):
        """Paste symbol into the target grid."""
        grid.fill_rect(self._startpos, self.grid)

    def remove(self, grid):
        """Remove the symbol from the target grid."""
        ul = self._startpos
        br = Pos(self._startpos.x + self.width, self._startpos.y + self.height)
        grid.erase_rect((ul, br))

    def mirror(self, grid):
        # mirror specific characters
        switcher = {'/': '\\',
                    '\\': '/',
                    '<': '>',
                    '>': '<',
                    '(': ')',
                    ')': '('
                    }
        mir_grid = []

        for r, row in enumerate(grid):
            rev = []
            for c in reversed(row):
                try:
                    rev.append(switcher[c])
                except KeyError:
                    rev.append(c)
            mir_grid.append(rev)

        return mir_grid


class Character(Symbol):

    def __init__(self, char, grid=None, startpos=None):

        id = ord(char)
        if grid is None:
            thegrid = {"N": [[char]]}
        else:
            thegrid = grid
        super(Character, self).__init__(id=id, grid=thegrid, startpos=startpos)

        self._char = char

    @property
    def grid(self):
        return self._grid[self.ORIENTATION[0]]

    def memo(self):
        str = "{0}:{1},{2}".format(CHARACTER, self._id, self._startpos)
        return str

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        return Character(self._char, grid=self._grid, startpos=startpos)

    def grid_next(self):
        # raise NotImplementedError
        return


class Text(Symbol):

    def __init__(self, pos, text):

        grid = {"N": [['?']]}
        super(Text, self).__init__(grid=grid, startpos=pos)

        self._text = text
        self._representation()

    def _representation(self):

        self._repr = dict()

        startpos = self._startpos
        pos = self._startpos
        incr = Pos(1, 0)

        str = self._text.split('\n')
        for line in str:
            pos.x = startpos.x
            for char in line:
                self._repr[pos] = char
                pos += incr
            pos += Pos(0, 1)

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
        return ObjectView(self._repr, self._startpos)

    def memo(self):
        jstext = json.dumps(self._text)
        str = "{0}:{1},{2}".format(TEXT, self._startpos, jstext)
        return str

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        return Text(pos=startpos, text=self._text)

    def grid_next(self):
        # raise NotImplementedError
        return

    def paste(self, grid):
        pos = self._startpos
        y = pos.y
        str = self._text.split('\n')
        for line in str:
            x = pos.x
            for char in line:
                x += 1
                grid.set_cell(Pos(x, y), char)
            y += 1  # TODO check boundary?

    def remove(self, grid):
        pos = self._startpos
        y = pos.y
        str = self._text.split('\n')
        for line in str:
            x = pos.x
            for char in line:
                x += 1
                grid.set_cell(Pos(x, y), ' ')
            y += 1  # TODO check boundary?


class Line(Symbol):

    def __init__(self, startpos, endpos, type='0'):

        super(Line, self).__init__(id=type, startpos=startpos, endpos=endpos)

        self._type = type
        self._terminal = TERMINAL_TYPE[type]

        self._direction()
        self._representation()

    def _direction(self):
        if self._startpos.x == self._endpos.x:
            self._dir = VERTICAL
        elif self._startpos.y == self._endpos.y:
            self._dir = HORIZONTAL
        else:
            self._dir = None

    def _representation(self):
        """Compose the line elements."""

        self._repr = dict()

        start = self._startpos
        end = self._endpos

        if start < end:
            pos = start
        else:
            pos = end
            end = start

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
        self._repr[pos] = terminal
        pos += incr

        # TODO make this one string (and support an appropriate fill method for this in grid)
        while pos < end:
            self._repr[pos] = line_char
            pos += incr

        # endpoint terminal
        self._repr[pos] = terminal

    def grid_next(self):
        # TODO enable to rotate (from HOR to VERT)?
        raise NotImplementedError

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        type = copy.deepcopy(self._type)
        return Line(startpos, endpos, type)

    def memo(self):
        str = "{0}:{1},{2},{3}".format(LINE, self._type, self._startpos, self._endpos)
        return str

    @property
    def view(self):
        return ObjectView(self._repr, self._startpos)

    @property
    def type(self):
        return self._type

    def paste(self, grid):

        first = True
        for pos, value in self._repr.items():
            # crossing lines
            if grid.cell(pos) in (LINE_HOR, LINE_VERT) and not first:
                grid.set_cell(pos, JUMP_CHAR)
            else:
                grid.set_cell(pos, value)
            first = False

    def remove(self, grid):
        for pos, value in self._repr.items():
            grid.set_cell(pos, ' ')


class MagLine(Line):

    def __init__(self, startpos, endpos, ml_endpos):

        # declare before super init as this is used in the representation method (called in super init)
        self._ml_endpos = ml_endpos

        super(MagLine, self).__init__(startpos=startpos, endpos=endpos)

    def _representation(self):

        line1 = Line(self._startpos, self._endpos)
        line2 = Line(self._endpos, self._ml_endpos)

        repr = dict()
        repr.update(line1._repr)

        # special char in the bend
        repr2 = line2._repr
        if self._endpos < self._ml_endpos:
            bend = list(repr2.keys())[0]
        else:
            bend = list(repr2.keys())[-1]
        repr2[bend] = ML_BEND_CHAR
        repr.update(repr2)

        self._repr = repr

    @property
    def ml_endpos(self):
        return self._ml_endpos

    @ml_endpos.setter
    def ml_endpos(self, value):
        self._ml_endpos = value
        self._representation()

    def grid_next(self):
        # TODO enable to rotate (from HOR to VERT)?
        raise NotImplementedError

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        ml_endpos = copy.deepcopy(self._ml_endpos)
        return MagLine(startpos, endpos, ml_endpos)

    def memo(self):
        str = "{0}:{1},{2},{3}".format(MAG_LINE, self._startpos, self._endpos, self._ml_endpos)
        return str


class Rect(Symbol):

    def __init__(self, startpos, endpos):

        super(Rect, self).__init__(startpos=startpos, endpos=endpos)

        self._representation()

    def _representation(self):

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

        repr = dict()

        repr.update(line1._repr)
        repr.update(line2._repr)
        repr.update(line3._repr)
        repr.update(line4._repr)
        self._repr = repr

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
        return ObjectView(self._repr, self._startpos)

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        return Rect(startpos, endpos)

    def memo(self):
        str = "{0}:{1},{2}".format(DRAW_RECT, self._startpos, self._endpos)
        return str

    def paste(self, grid):

        start = self._startpos
        end = self._endpos

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

        line1.paste(grid)
        line2.paste(grid)
        line3.paste(grid)
        line4.paste(grid)

    def remove(self, grid):

        start = self._startpos
        end = self._endpos

        ul = start
        ur = Pos(end.x, start.y)
        bl = Pos(start.x, end.y)
        br = end

        type = '3'

        line1 = Line(ul, ur, type)
        line2 = Line(ur, br, type)
        line3 = Line(bl, br, type)
        line4 = Line(ul, bl, type)

        line1.remove(grid)
        line2.remove(grid)
        line3.remove(grid)
        line4.remove(grid)


class Column(Symbol):

    def __init__(self, col, action):

        self._col = col
        self._action = action

        super(Column, self).__init__(id=col, startpos=Pos(col, 0))

    @property
    def col(self):
        return self._col

    def memo(self):
        if self._action == INSERT:
            str = "i"
        else:
            str = "d"

        str += "{0}:{1}".format(COL, self.col)
        return str


class Row(Symbol):

    def __init__(self, row, action):

        self._row = row
        self._action = action

        super(Row, self).__init__(id=row, startpos=Pos(0, row))

    @property
    def row(self):
        return self._row

    def memo(self):
        if self._action == INSERT:
            str = "i"
        else:
            str = "d"

        str += "{0}:{1}".format(ROW, self.row)
        return str
