'''
AACircuit
2020-03-02 JvO
'''

import copy
import json
import collections
from pubsub import pub
from bresenham import bresenham
from math import pi, radians, atan

from application import _
from application.pos import Pos
from application import FONTSIZE
from application import INSERT, COL, ROW
from application import HORIZONTAL, VERTICAL, LONGEST_FIRST
from application import LINE_HOR, LINE_VERT
from application import TERMINAL_TYPE
from application import COMPONENT, CHARACTER, TEXT, DRAW_RECT, LINE, MAG_LINE, DIR_LINE


# TODO how to get this into an 'utility' source
# TODO now has a duplicate in symbol.py

def show_text(ctx, x, y, text):
    """Show text on a canvas position taking into account the Cairo glyph origin."""

    # the Cairo text glyph origin is its left-bottom corner
    y += FONTSIZE

    ctx.move_to(x, y)
    ctx.show_text(text)
    return


class Symbol(object):
    """
    Symbol represented by a grid.

    :param id: the component id
    :param dict: the character-grid to create the symbol
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

    def __str__(self):
        str = _("symbol id: {0} orientation: {1}").format(self._id, self.ORIENTATION[self._ori])
        return str

    def _representation(self):

        self._repr = dict()

        pos = self._startpos
        incr = Pos(1, 0)

        for row in self.grid:
            pos.x = self._startpos.x
            for char in row:
                self._repr[pos] = char
                pos += incr
            pos += Pos(0, 1)

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
    def default(self):
        # default provides one ("N" orientation) grid only
        grid = {'N': [
            ' ___ ',
            '|__ \\',
            '  / /',
            ' |_| ',
            ' (_) ']}
        return grid

    @property
    def repr(self):
        return self._repr

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

    def rotate(self):
        """Return the grid with the next (90° clockwise rotated) orientation for this symbol."""
        self._ori += 1
        self._ori %= 4

        return self.grid

    def draw(self, ctx, pos=None):
        """
        Draw the symbol on the grid canvas.
        :param ctx: the Cairo context
        :param pos: target position in grid canvas (x,y) coordinates
        """
        self._representation()

        if pos is None:
            pos = self._startpos.view_xy()

        offset = pos - self._startpos.view_xy()
        for pos, char in self._repr.items():
            grid_pos = pos.view_xy() + offset
            show_text(ctx, grid_pos.x, grid_pos.y, char)

    def paste(self, grid):
        self._representation()

        """Paste symbol into the target grid."""
        for pos, value in self._repr.items():
            grid.set_cell(pos, value)

    def remove(self, grid):
        """Remove the symbol from the target grid."""
        for pos in self._repr.keys():
            grid.set_cell(pos, ' ')  # TODO use CONSTANT value

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

        self._representation()

    @property
    def grid(self):
        return self._grid[self.ORIENTATION[0]]

    def memo(self):
        str = "{0}:{1},{2}".format(CHARACTER, self._id, self._startpos)
        return str

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        return Character(self._char, grid=self._grid, startpos=startpos)

    def rotate(self):
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

    def memo(self):
        jstext = json.dumps(self._text)
        str = "{0}:{1},{2}".format(TEXT, self._startpos, jstext)
        return str

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        return Text(pos=startpos, text=self._text)

    def rotate(self):
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
                if char != ' ':
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
    """A horizontal or verical line from start to end position."""

    def __init__(self, startpos, endpos, type=None):

        super(Line, self).__init__(id=type, startpos=startpos, endpos=endpos)

        if type is None:
            self._type = 0
        else:
            self._type = type
        self._terminal = TERMINAL_TYPE[self._type]

        self._direction()
        self._representation()

    def _direction(self):
        dx, dy = (self._endpos - self._startpos).xy
        if abs(dx) > abs(dy):
            self._dir = HORIZONTAL
        else:
            self._dir = VERTICAL

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

        while pos < end:
            self._repr[pos] = line_char
            pos += incr

        # endpoint terminal
        self._repr[pos] = terminal

    def rotate(self):
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
    def type(self):
        return self._type

    def remove(self, grid):
        for pos, value in self._repr.items():
            grid.set_cell(pos, ' ')  # TODO use CONSTANT


class DirLine(Line):
    """A straight line from start to end position."""

    def __init__(self, startpos, endpos):

        super(DirLine, self).__init__(startpos=startpos, endpos=endpos)

        self._representation()

    def _representation(self):

        x, y = (self._endpos - self._startpos).xy

        # TODO better represenation of straight line (using ASCII chars)?

        if abs(x) > 0:
            angle = atan(y / x)
        else:
            angle = pi / 2

        if angle < radians(-75):
            linechar = '|'
        if angle >= radians(-75) and angle <= radians(-52):
            linechar = '.'
        elif angle > radians(-52) and angle <= radians(-37):
            linechar = '/'
        elif angle > radians(-37) and angle <= radians(-15):
            linechar = '.'
        elif angle > radians(-15) and angle <= radians(15):
            linechar = '-'
        elif angle > radians(15) and angle <= radians(37):
            linechar = '.'
        elif angle > radians(37) and angle <= radians(52):
            linechar = '\\'
        elif angle > radians(52) and angle <= radians(75):
            linechar = '.'
        elif angle > radians(75):
            linechar = '|'
        else:
            linechar = '?'

        repr = dict()

        line = bresenham(self._startpos.x, self._startpos.y, self._endpos.x, self._endpos.y)

        for coord in line:
            pos = Pos(coord[0], coord[1])
            repr[pos] = linechar

        self._repr = repr

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        return DirLine(startpos, endpos)

    def memo(self):
        str = "{0}:{1},{2}".format(DIR_LINE, self._startpos, self._endpos)
        return str


class MagLine(Line):
    """A square bend from start to end position."""

    # TODO move to preferences

    LineMatchingData = collections.namedtuple('line_matching_data', ['pattern', 'ori', 'char'])

    LMD = []
    LMD.append(LineMatchingData(
        [[' ', ' ', ' '],
         [' ', ' ', ' '],
         [' ', ' ', ' ']], LONGEST_FIRST, 'o'))
    LMD.append(LineMatchingData(
        [['x', 'x', 'x'],
         ['-', 'x', '-'],
         ['x', 'x', 'x']], VERTICAL, 'o'))
    LMD.append(LineMatchingData(
        [['x', '|', 'x'],
         ['x', 'x', 'x'],
         ['x', '|', 'x']], HORIZONTAL, 'o'))
    LMD.append(LineMatchingData(
        [['x', 'x', 'x'],
         ['x', 'x', '-'],
         ['x', 'x', 'x']], HORIZONTAL, '-'))
    LMD.append(LineMatchingData(
        [['x', 'x', 'x'],
         ['-', 'x', 'x'],
         ['x', 'x', 'x']], HORIZONTAL, '-'))
    LMD.append(LineMatchingData(
        [['x', 'x', 'x'],
         ['x', 'x', 'x'],
         [' ', '|', ' ']], VERTICAL, '|'))
    LMD.append(LineMatchingData(
        [[' ', '|', ' '],
         ['x', 'x', 'x'],
         ['x', 'x', 'x']], VERTICAL, '|'))
    LMD.append(LineMatchingData(
        [['x', 'x', 'x'],
         ['x', 'x', 'x'],
         ['x', '|', 'x']], HORIZONTAL, '.'))
    LMD.append(LineMatchingData(
        [['x', '|', 'x'],
         ['x', 'x', 'x'],
         ['x', 'x', 'x']], HORIZONTAL, "'"))
    LMD.append(LineMatchingData(
        [['x', 'x', 'x'],
         ['x', '|', 'x'],
         ['x', 'x', 'x']], VERTICAL, '|'))

    def __init__(self, startpos, endpos, cell_callback=None):

        self.cell = cell_callback

        super(MagLine, self).__init__(startpos=startpos, endpos=endpos)

        self._representation()

    def _line_match(self, idx, search_dir, pos):
        """
        Match a character in the grid against a Magic Line pattern.

        :param idx: number of the line matching pattern to be used
        :param search_dir: search direction
        :param pos: character position (col, row) coordinates

        :return result: True if a match was found, otherwise False
        :return ori: magic line orientation
        :return char: corner character

        """
        lmd = self.LMD[idx]

        result = True
        m_ori = None
        m_char = None

        if pos > Pos(0, 0) and (search_dir is None or search_dir == lmd.ori):

            for j, row in enumerate(lmd.pattern):
                for i, char in enumerate(row):
                    if char != 'x':
                        m_pos = pos + Pos(i - 1, j - 1)
                        m_cell = self.cell(m_pos)

                        if m_cell == chr(0):  # TODO x00 and x32 (space)
                            m_cell = chr(32)

                        if m_cell != char:
                            result = False
                            break
            if result:
                m_ori = lmd.ori
                m_char = lmd.char
                # print("line_match, idx:", idx, " m_ori:", m_ori, " m_char:", m_char)

        else:
            result = False

        return result, m_ori, m_char

    def _representation(self):

        startpos = self._startpos
        endpos = self._endpos

        dx = abs(endpos.x - startpos.x)
        dy = abs(endpos.y - startpos.y)

        self._repr = dict()

        f_ori = None
        f_terminal = None

        s_ori = HORIZONTAL

        # determine the terminal of the first line
        for i in range(len(self.LMD)):
            match, f_ori, f_terminal = self._line_match(i, None, startpos)
            if match:
                self._repr[startpos] = f_terminal
                break

        # determine the orientation of the first line
        if f_ori == LONGEST_FIRST:
            if dy > dx:
                f_ori = VERTICAL
            else:
                f_ori = HORIZONTAL

        # TODO Move this to view
        # msg = _("Start: D[{0}] char:{1} ori:{2}".format(i, f_terminal, f_ori))
        # pub.sendMessage('STATUS_MESSAGE', msg=msg)

        # determine the orientation of the second line
        if f_ori == HORIZONTAL:
            if dy > 0:
                s_ori = VERTICAL
            else:
                s_ori = HORIZONTAL

        elif f_ori == VERTICAL:
            if dx > 0:
                s_ori = HORIZONTAL
            else:
                s_ori = VERTICAL

        for i in range(len(self.LMD)):
            match, m_ori, m_terminal = self._line_match(i, s_ori, endpos)
            if match:
                # the end-terminal of the second line
                self._repr[endpos] = m_terminal
                break

        # TODO Move this to view
        # msg = _("End: D[{0}] char:{1} ori:{2}".format(i, m_terminal, m_ori))
        # pub.sendMessage('STATUS_MESSAGE', msg=msg)

        self._corner_line(f_ori)

    def _corner_line(self, ori):

        startpos = self._startpos
        endpos = self._endpos

        dx, dy = (endpos - startpos).xy

        # TODO use CONSTANTs
        if (dy >= 0) ^ (ori != VERTICAL):
            corner_char = "'"  # lower corner x39
        else:
            corner_char = '.'  # upper corner x46

        top = 0
        left = 0

        if ori == HORIZONTAL:
            top = startpos.y
            left = endpos.x

        elif ori == VERTICAL:
            top = endpos.y
            left = startpos.x

        # horizontal line
        if dx > 0:
            startv = startpos.x + 1  # don't overwrite the terminal char (in the startposition)
            endv = endpos.x
        else:
            startv = endpos.x + 1  # don't overwrite the terminal char (in the startposition)
            endv = startpos.x

        if abs(dx) > 1:
            for temp in range(endv - startv):
                pos = Pos(startv + temp, top)
                # TODO use CONSTANTs
                if self.cell(pos) == '|':  # x124
                    char = ')'
                else:
                    char = '-'
                self._repr[pos] = char

        # vertical line
        if dy > 0:
            startv = startpos.y + 1  # don't overwrite the terminal char (in the startposition)
            endv = endpos.y
        else:
            startv = endpos.y + 1  # don't overwrite the terminal char (in the startposition)
            endv = startpos.y

        if abs(dy) > 1:
            for temp in range(endv - startv):
                pos = Pos(left, startv + temp)
                # TODO use CONSTANTs
                if self.cell(pos) == '-':  # x45
                    char = ')'
                else:
                    char = '|'
                self._repr[pos] = char

        # corner character, if there is a corner
        if (ori == HORIZONTAL and abs(dy) > 0) or (ori == VERTICAL and abs(dx) > 0):
            self._repr[Pos(left, top)] = corner_char

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        return MagLine(startpos, endpos, self.cell)

    def memo(self):
        str = "{0}:{1},{2},{3}".format(MAG_LINE, self._startpos, self._endpos)
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

        type = 3

        line1 = Line(ul, ur, type)
        line2 = Line(ur, br, type)
        line3 = Line(bl, br, type)
        line4 = Line(ul, bl, type)

        self._repr = dict()

        self._repr.update(line1.repr)
        self._repr.update(line2.repr)
        self._repr.update(line3.repr)
        self._repr.update(line4.repr)

    def rotate(self):

        w = self._endpos.x - self._startpos.x
        h = self._endpos.y - self._startpos.y

        ul = self._startpos
        br = Pos(self._startpos.x + h, self._startpos.y + w)

        self._startpos = ul
        self._endpos = br

        # TODO
        # self._rect()

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        return Rect(startpos, endpos)

    def memo(self):
        str = "{0}:{1},{2}".format(DRAW_RECT, self._startpos, self._endpos)
        return str

    def paste(self, grid):

        self._representation()

        start = self._startpos
        end = self._endpos

        ul = start
        ur = Pos(end.x, start.y)
        bl = Pos(start.x, end.y)
        br = end

        # print("ul:", ul, " ur:", ur, "\nbl:", bl, "br:", br)

        type = 3

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

        type = 3

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
