'''
AACircuit
2020-03-02 JvO
'''

import copy
import json
import re
from pubsub import pub
from bresenham import bresenham
from math import pi, radians, atan

from locale import gettext as _
from application.preferences import Preferences
from application.magic_line_settings import MagicLineSettings
from application.pos import Pos
from application import CELL_ERASE
from application import INSERT, COL, ROW
from application import HORIZONTAL, VERTICAL, LONGEST_FIRST
from application import ERASER, COMPONENT, CHARACTER, TEXT, DRAW_RECT, LINE, MAG_LINE, DIR_LINE, ARROW


def show_text(ctx, x, y, text):
    """Show text on a canvas position taking into account the Cairo glyph origin."""
    # the Cairo text glyph origin is its left-bottom corner
    y += Preferences.values['FONTSIZE']
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
        self._has_pickpoint = True
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
        self._is_symbol = True
        self._is_text = False
        self._is_line = False

    def __str__(self):
        str = _("Class: {0} id: {1} ori: {2} startpos: {3}").format(self.__class__.__name__, self._id, self.ORIENTATION[self._ori], self.startpos)
        return str

    def _representation(self):
        self._repr = dict()
        pos = self._startpos
        incr = Pos(1, 0)
        for row in self.grid:
            pos.x = self._startpos.x
            for char in row:
                if char != ' ':
                    self._repr[pos] = char
                pos += incr
            pos += Pos(0, 1)

    @property
    def name(self):
        return self.__class__.__name__

    @property
    def is_symbol(self):
        return self._is_symbol

    @property
    def is_text(self):
        return self._is_text

    @property
    def is_line(self):
        return self._is_line

    @property
    def has_pickpoint(self):
        return self._has_pickpoint

    @property
    def pickpoint_pos(self):
        """
        Return the pick position.

        Examples, where '.' represents a space character and 'x' the pick-point:
        '.|.....' => 'x|.....'
        '....|..' => '...x|..'
        '|......' => 'x|......'
        '.......' => '.......x' => empty first line not expected, see the component library content

        """
        first_row = self.grid[0]
        found = re.search(r'\S', first_row)
        if found:
            x_offset = found.start()
            x_offset -= 1
        else:
            x_offset = 0
        pos = Pos(self._startpos.x + x_offset, self._startpos.y)
        return pos

    @property
    def id(self):
        return self._id

    @property
    def ori_as_str(self):
        return Symbol.ORIENTATION[self._ori]

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
        """Set to True to show the symbol vertically mirrored, otherwise False."""
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
        """
        The representation in ASCII characters of the symbol on a grid.
        :returns a dictionary of positions in grid (col,row) coordinates and the character to be shown on each position.
        """
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
        try:
            if self._mirrored == 1:
                return self.mirror(self._grid[self.ORIENTATION[self._ori]])
            else:
                return self._grid[self.ORIENTATION[self._ori]]
        except KeyError:
            return self.default[self.ORIENTATION[0]]

    def rotate(self):
        """Return the grid with the next (90 degrees clockwise rotated) orientation for this symbol."""
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
        """Paste the symbol in the target grid at its start position."""
        self._representation()
        for pos, value in self._repr.items():
            grid.set_cell(pos, value)

    def remove(self, grid):
        """Remove the symbol from the target grid."""
        self._representation()
        for pos in self._repr.keys():
            grid.set_cell(pos, CELL_ERASE)

    def mirror(self, grid):
        """Return the symbol grid vertically mirrored."""
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
            rev = ""
            for c in reversed(row):
                try:
                    rev += switcher[c]
                except KeyError:
                    rev += c
            mir_grid.append(rev)
        return mir_grid


class Eraser(Symbol):

    def __init__(self, size, startpos=None):
        """
        Hide a part of the grid.

        :param size: the size (in cols, rows) of the grid area to be erased
        :param startpos: the upper-left corner (col,row) coordinate of the area to be erased
        """
        super(Eraser, self).__init__(grid=None, startpos=startpos)
        self._size = size
        self._representation()

    def _representation(self):
        self._repr = dict()
        pos = self._startpos
        incr = Pos(1, 0)
        for row in range(self._size[1]):
            pos.x = self._startpos.x
            for col in range(self._size[0]):
                self._repr[pos] = CELL_ERASE
                pos += incr
            pos += Pos(0, 1)

    def draw(self, ctx, pos=None):
        """
        :param ctx: the Cairo context
        :param pos: target position in grid canvas (x,y) coordinates
        """
        ctx.save()
        ctx.set_source_rgb(0.75, 0.75, 0.75)
        x_start, y_start = pos.xy
        # size from grid (col,row) to view (x,y) coordinates
        size = Pos(self._size[0], self._size[1]).view_xy()
        width = size.x
        height = size.y
        ctx.rectangle(x_start, y_start, width, height)
        ctx.fill()
        ctx.restore()

    def memo(self):
        """Return entry for the actions as recorded in the memo."""
        str = "{0}:{1},{2},{3}".format(ERASER, self._size[0], self._size[1], self._startpos)
        return str

    def copy(self):
        return Eraser(size=self._size, startpos=self._startpos)


class Character(Symbol):

    def __init__(self, char, grid=None, startpos=None):
        id = ord(char)
        if grid is None:
            thegrid = {'N': [char]}
        else:
            thegrid = grid
        super(Character, self).__init__(id=id, grid=thegrid, startpos=startpos)
        self._char = char
        self._is_symbol = False
        self._is_text = True
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
        pass


class Text(Symbol):

    def __init__(self, pos, text, ori=0):
        grid = {"N": ['?']}
        super(Text, self).__init__(grid=grid, ori=ori, startpos=pos)
        self._text = text
        self._is_symbol = False
        self._is_text = True
        self._representation()

    def _representation(self):
        self._repr = dict()
        startpos = self._startpos
        pos = self._startpos
        str = self._text.split('\n')
        if self._ori == 0 or self._ori == 2:
            for line in str:
                pos.x = startpos.x
                for char in line:
                    if char != ' ':
                        self._repr[pos] = char
                    pos += Pos(1, 0)
                pos += Pos(0, 1)
        elif self._ori == 1 or self._ori == 3:
            for line in str:
                pos.y = startpos.y
                for char in line:
                    if char != ' ':
                        self._repr[pos] = char
                    pos += Pos(0, 1)
                pos += Pos(1, 0)

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
        str = "{0}:{1},{2},{3}".format(TEXT, self._ori, self._startpos, jstext)
        return str

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        ori = copy.deepcopy(self._ori)
        return Text(pos=startpos, text=self._text, ori=ori)


class Line(Symbol):
    """A horizontal or verical line from start to end position."""
    # decimal char codes (following the original AACircuit) for lines
    # and 0/1 for the 'old' respectively new Magic line
    MLINE_LEGACY = 0
    MLINE = 1
    LINE1 = 0
    LINE2 = ord('o')  # 111
    LINE3 = ord('+')  # 43
    LINE4 = ord("'")  # 39
    TERMINAL_TYPE = {MLINE: None,
                     LINE1: Preferences.values['TERMINAL1'],
                     LINE2: Preferences.values['TERMINAL2'],
                     LINE3: Preferences.values['TERMINAL3'],
                     LINE4: Preferences.values['TERMINAL4']}

    def __init__(self, startpos, endpos, type=None):
        grid = {"N": ['?']}
        super(Line, self).__init__(id=type, grid=grid, startpos=startpos, endpos=endpos)
        if type is None:
            self._type = Line.LINE1
        else:
            self._type = type
        self._terminal = self.TERMINAL_TYPE[self._type]
        self._is_symbol = False
        self._is_line = True
        self._representation()

    def _direction(self):
        dx, dy = (self._endpos - self._startpos).xy
        if abs(dx) > abs(dy):
            self._dir = HORIZONTAL
        else:
            self._dir = VERTICAL

    def _representation(self):
        """Compose the line elements."""
        self._direction()
        self._repr = dict()
        terminal = self._terminal
        start_terminal = terminal
        start = self._startpos
        end = self._endpos
        pos = start
        if self._dir == HORIZONTAL:
            line_char = Preferences.values['LINE_HOR']
            incr = Pos(1, 0)
            if start > end:
                # line drawn from right-to-left
                pos = Pos(end.x, start.y)
                end = start

        elif self._dir == VERTICAL:
            if self._type == self.LINE4:
                start_terminal = Preferences.values['TERMINAL4_VERT']
            line_char = Preferences.values['LINE_VERT']
            incr = Pos(0, 1)
            if start > end:
                # line drawn from right-to-left
                pos = Pos(start.x, end.y)
                end = start
        else:
            line_char = "?"
            incr = Pos(1, 1)

        # startpoint terminal
        if start_terminal is None:
            self._repr[pos] = line_char
        else:
            self._repr[pos] = start_terminal
        pos += incr
        while pos < end:
            self._repr[pos] = line_char
            pos += incr
        # endpoint terminal
        if self._terminal is None:
            self._repr[pos] = line_char
        else:
            self._repr[pos] = self._terminal

    @property
    def pickpoint_pos(self):
        return self.startpos

    def rotate(self):
        # TODO enable to rotate (from HOR to VERT)?
        pass

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


class DirLine(Line):
    """A straight line from start to end position."""

    def __init__(self, startpos, endpos):
        super(DirLine, self).__init__(startpos=startpos, endpos=endpos)
        self._representation()

    def _representation(self):
        x, y = (self._endpos - self._startpos).xy
        # TODO better representation of straight line (using ASCII chars)?
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

    ori_desc = {0: 'hor', 1: 'vert', 2: 'longest-first', None: 'None'}

    def __init__(self, startpos, endpos, cell_callback=None, type=Line.MLINE):
        self.cell = cell_callback
        super(MagLine, self).__init__(startpos=startpos, endpos=endpos, type=type)
        self._representation()

    def _line_match(self, idx, ori, pos):
        """
        Match a character in the grid against a Magic Line pattern.

        :param idx: number of the line matching pattern to be used
        :param ori: orientation of the line to be drawn
        :param pos: character position (col, row) coordinates

        :return result: True if a match was found, otherwise False
        :return ori: magic line orientation
        :return char: terminal character

        """
        lmd = MagicLineSettings.LMD[idx]
        result = True
        m_ori = None
        m_char = None
        if pos > Pos(0, 0) and (ori is None or ori == lmd.ori):
            for j, row in enumerate(lmd.pattern):
                for i, char in enumerate(row):
                    if char != 'x':
                        m_pos = pos + Pos(i - 1, j - 1)
                        m_cell = self.cell(m_pos)
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
        dx = endpos.x - startpos.x
        dy = endpos.y - startpos.y
        self._repr = dict()
        f_ori = None
        f_terminal = None
        s_ori = HORIZONTAL

        # determine the first line terminal
        for i in range(len(MagicLineSettings.LMD)):
            match, f_ori, f_terminal = self._line_match(i, None, startpos)
            if match:
                self._repr[startpos] = f_terminal
                break
        # the orientation of the first line
        if f_ori is None:
            f_ori = HORIZONTAL
        elif f_ori == LONGEST_FIRST:
            if abs(dy) > abs(dx):
                f_ori = VERTICAL
            else:
                f_ori = HORIZONTAL
        msg = _("Start: M[{0}] char:{1} ori:{2} / ").format(i, f_terminal, MagLine.ori_desc[f_ori])

        # the orientation of the second line
        if f_ori == HORIZONTAL:
            if abs(dy) > 0:
                s_ori = VERTICAL
            else:
                s_ori = HORIZONTAL
        elif f_ori == VERTICAL:
            if abs(dx) > 0:
                s_ori = HORIZONTAL
            else:
                s_ori = VERTICAL
        for i in range(len(MagicLineSettings.LMD)):
            match, m_ori, m_terminal = self._line_match(i, s_ori, endpos)
            if match:
                # the end-terminal of the second line
                self._repr[endpos] = m_terminal
                break
        msg += _("End: M[{0}] char:{1} ori:{2}").format(i, m_terminal, MagLine.ori_desc[m_ori])
        pub.sendMessage('STATUS_MESSAGE', msg=msg)
        self._corner_line(f_ori)

    def _corner_line(self, ori):
        startpos = self._startpos
        endpos = self._endpos
        dx = endpos.x - startpos.x
        dy = endpos.y - startpos.y
        if (dy >= 0) ^ (ori != VERTICAL):
            corner_char = Preferences.values['LOWER_CORNER']
        else:
            corner_char = Preferences.values['UPPER_CORNER']
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
                if self.cell(pos) == Preferences.values['LINE_VERT']:
                    char = Preferences.values['CROSSING']
                else:
                    char = Preferences.values['LINE_HOR']
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
                if self.cell(pos) == Preferences.values['LINE_HOR']:
                    char = Preferences.values['CROSSING']
                else:
                    char = Preferences.values['LINE_VERT']
                self._repr[pos] = char

        # corner character, if there is a corner
        if (ori == HORIZONTAL and abs(dy) > 0) or (ori == VERTICAL and abs(dx) > 0):
            self._repr[Pos(left, top)] = corner_char

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        return MagLine(startpos, endpos, self.cell, self.type)

    def memo(self):
        str = "{0}:{1},{2},{3}".format(MAG_LINE, self._type, self._startpos, self._endpos)
        return str


class MagLineOld(MagLine):
    """Alte MagLine, wegen abwaertscompatibilitaet noch vorhanden."""

    def __init__(self, startpos, endpos, cell_callback=None, type=Line.MLINE_LEGACY):
        super(MagLineOld, self).__init__(startpos=startpos, endpos=endpos, cell_callback=cell_callback, type=type)
        self._representation()
        self._se_count = 0
        self._se_status_msg = ""

    def paste(self, grid):
        super(MagLineOld, self).paste(grid)
        if self._se_count > 0:
            msg = self._status_msg
            pub.sendMessage('STATUS_MESSAGE', msg=msg)

    def _representation(self):
        se_status = ""
        se_count = 0
        se_count, se_status, start_char, start_ori = self.start_character(se_count, se_status)
        se_count, se_status, end_char = self.end_character(se_count, se_status, start_ori)
        self._se_count = se_count
        self._status_msg = se_status + "; cnt:" + str(se_count)
        self._draw_line(start_char, start_ori, end_char)

    def start_character(self, se_count, se_status):

        def set_rechts_links():
            nonlocal start_ori  # noqa E999
            nonlocal start_char  # noqa E999
            start_ori = HORIZONTAL
            start_char = line_hor

        def set_oben_unten():
            nonlocal start_ori  # noqa E999
            nonlocal start_char  # noqa E999
            start_ori = VERTICAL
            start_char = line_vert

        x1, y1 = self._startpos.xy
        x2, y2 = self._endpos.xy
        xdiv = abs(x2 - x1)  # Differenz x
        ydiv = abs(y2 - y1)  # Differenz y
        start_ori = VERTICAL
        start_char = '#'
        space_char = ' '
        connect_char = 'o'
        line_hor = Preferences.values['LINE_HOR']
        line_vert = Preferences.values['LINE_VERT']
        upper_corner = Preferences.values['UPPER_CORNER']
        lower_corner = Preferences.values['LOWER_CORNER']

        # DEBUG
        # print("START startc: {} endc: {} o: {} u: {} l:{} r:{} ".format(startc, endc,
        #                                                                 self.cell(Pos(x1, y1 - 1)),
        #                                                                 self.cell(Pos(x1, y1 + 1)),
        #                                                                 self.cell(Pos(x1 - 1, y1)),
        #                                                                 self.cell(Pos(x1 + 1, y1))))

        # nichts drumherum
        if self.cell(Pos(x1 - 1, y1)) == space_char \
                and self.cell(Pos(x1 + 1, y1)) == space_char \
                and self.cell(Pos(x1, y1 - 1)) == space_char \
                and self.cell(Pos(x1, y1 + 1)) == space_char:
            if xdiv > ydiv:
                start_ori = HORIZONTAL
            else:
                start_ori = VERTICAL
            if start_ori == VERTICAL:
                start_char = line_vert
            else:
                start_char = line_hor
            se_count += 1
            se_status = _("S:all free")

        # o/u = |, l/r frei
        if (self.cell(Pos(x1, y1 - 1)) == line_vert or self.cell(Pos(x1, y1 + 1)) == line_vert) \
                and self.cell(Pos(x1 - 1, y1)) == space_char \
                and self.cell(Pos(x1 + 1, y1)) == space_char:
            if ydiv > 0:
                set_oben_unten()
            elif ydiv == 0:
                start_ori = HORIZONTAL
                if self.cell(Pos(x1, y1 - 1)) == line_vert:
                    start_char = lower_corner
                if self.cell(Pos(x1, y1 + 1)) == line_vert:
                    start_char = upper_corner
            se_count += 1
            se_status = _("S:topVbottom {}; l/r=space").format(line_vert)

        # oben .
        if self.cell(Pos(x1, y1 - 1)) == upper_corner \
                and self.cell(Pos(x1, y1 + 1)) == space_char \
                and self.cell(Pos(x1 - 1, y1)) == space_char \
                and self.cell(Pos(x1 + 1, y1)) == space_char:
            if ydiv > 0:
                set_oben_unten()
            elif ydiv == 0:
                set_rechts_links()
            se_count += 1
            se_status = _("S:top {}; l/r/b=space").format(lower_corner)

        # unten '
        if self.cell(Pos(x1, y1 + 1)) == lower_corner \
                and self.cell(Pos(x1, y1 - 1)) == space_char \
                and self.cell(Pos(x1 - 1, y1)) == space_char \
                and self.cell(Pos(x1 + 1, y1)) == space_char:
            if ydiv > 0:
                set_oben_unten()
            elif ydiv == 0:
                set_rechts_links()
            se_count += 1
            se_status = _("S:bottom {}; l/r/t=space").format(lower_corner)

        # oben -
        if self.cell(Pos(x1, y1 - 1)) == line_hor \
                and self.cell(Pos(x1, y1 + 1)) == space_char \
                and self.cell(Pos(x1 - 1, y1)) == space_char \
                and self.cell(Pos(x1 + 1, y1)) == space_char:
            if ydiv > 0:
                set_oben_unten()
            elif ydiv == 0:
                set_rechts_links()
            se_count += 1
            se_status = _("S:top {}; l/r/b=space").format(line_hor)

        # unten -
        if self.cell(Pos(x1, y1 + 1)) == line_hor \
                and self.cell(Pos(x1, y1 - 1)) == space_char \
                and self.cell(Pos(x1 - 1, y1)) == space_char \
                and self.cell(Pos(x1 + 1, y1)) == space_char:
            if ydiv > 0:
                set_oben_unten()
            elif ydiv == 0:
                set_rechts_links()
            se_count += 1
            se_status = _("S:bottom {}; l/r=space").format(line_hor)

        # l/r = -, o/u frei
        if (self.cell(Pos(x1 - 1, y1)) == line_hor or self.cell(Pos(x1 + 1, y1)) == line_hor) \
                and ((self.cell(Pos(x1, y1 - 1)) == space_char) or self.cell(Pos(x1, y1 + 1)) == space_char):
            if xdiv > 0:
                set_rechts_links()
            elif xdiv == 0:
                start_ori = VERTICAL
                if y2 > y1:
                    start_char = upper_corner
                elif y2 < y1:
                    start_char = lower_corner
            se_count += 1
            se_status = _("S:leftVright {}, topVbottom=space").format(line_hor)

        # links und rechts -, oben kein |
        if self.cell(Pos(x1 - 1, y1)) == line_hor \
                and self.cell(Pos(x1 + 1, y1)) == line_hor \
                and self.cell(Pos(x1, y1 - 1)) != line_vert:
            start_ori = VERTICAL
            start_char = connect_char
            se_count += 1
            se_status = _("S:left and right {}; top none {}").format(line_hor, line_vert)

        # oben und unten |, links kein -
        if self.cell(Pos(x1, y1 - 1)) == line_vert \
                and self.cell(Pos(x1, y1 + 1)) == line_vert \
                and self.cell(Pos(x1 - 1, y1)) != line_hor:
            start_ori = HORIZONTAL
            start_char = connect_char
            se_count += 1
            se_status = _("S:top and bottom {}; left none").format(line_vert, line_hor)

        # links oder rechts o
        if self.cell(Pos(x1 - 1, y1)) == connect_char \
                or self.cell(Pos(x1 + 1, y1)) == connect_char:
            set_rechts_links()
            se_count += 1
            se_status = _("S:leftVright {};").format(connect_char)

        # oben oder unten o
        if self.cell(Pos(x1, y1 - 1)) == connect_char \
                or self.cell(Pos(x1, y1 + 1)) == connect_char:
            set_oben_unten()
            se_count += 1
            se_status = _("S:topVbottom {};").format(connect_char)

        # generell, wenn startc noch # ist
        if start_char == '#':
            if start_ori == VERTICAL:
                start_char = line_vert
            elif start_ori == HORIZONTAL:
                start_char = line_hor

        return se_count, se_status, start_char, start_ori

    def end_character(self, se_count, se_status, start_ori):
        x1, y1 = self._startpos.xy
        x2, y2 = self._endpos.xy
        end_char = '#'
        space_char = ' '
        connect_char = 'o'
        line_hor = Preferences.values['LINE_HOR']
        line_vert = Preferences.values['LINE_VERT']
        upper_corner = Preferences.values['UPPER_CORNER']
        lower_corner = Preferences.values['LOWER_CORNER']

        # DEBUG
        # print("END type: {} startc: {} endc: {} o: {} u: {} l:{} r:{} ".format(self._type, startc, endc,
        #                                                                        self.cell(Pos(x2, y2 - 1)),
        #                                                                        self.cell(Pos(x2, y2 + 1)),
        #                                                                        self.cell(Pos(x2 - 1, y2)),
        #                                                                        self.cell(Pos(x2 + 1, y2))))

        # nichts drumherum
        if self.cell(Pos(x2 - 1, y2)) == space_char \
                and self.cell(Pos(x2 + 1, y2)) == space_char \
                and self.cell(Pos(x2, y2 - 1)) == space_char \
                and self.cell(Pos(x2, y2 + 1)) == space_char:
            if start_ori == VERTICAL:
                if x1 == x2:
                    end_char = line_vert
                else:
                    end_char = line_hor
            if start_ori == HORIZONTAL:
                if y1 == y2:
                    end_char = line_hor
                else:
                    end_char = line_vert
            se_count += 1
            se_status = _("E:all free")

        # von oben oder unten
        if (self.cell(Pos(x2, y2 - 1)) == line_vert or self.cell(Pos(x2, y2 + 1)) == line_vert) \
                and self.cell(Pos(x2 - 1, y2)) == space_char \
                and self.cell(Pos(x2 + 1, y2)) == space_char:
            if start_ori == VERTICAL:
                if x1 == x2:
                    end_char = line_vert
                else:
                    end_char = connect_char
            if start_ori == HORIZONTAL:
                if y1 == y2:
                    end_char = connect_char
                else:
                    end_char = line_vert
            se_count += 1
            se_status = _("E:top/bottom")

        # von links oder rechts
        if (self.cell(Pos(x2 - 1, y2)) == line_hor or self.cell(Pos(x2 + 1, y2)) == line_hor) \
                and self.cell(Pos(x2, y2 - 1)) == space_char \
                and self.cell(Pos(x2, y2 + 1)) == space_char:
            if start_ori == VERTICAL:
                if x1 == x2:
                    if y1 < y2:
                        end_char = lower_corner
                    if y1 > y2:
                        end_char = upper_corner
                else:
                    end_char = line_hor
            if start_ori == HORIZONTAL:
                if y1 != y2:
                    if y1 < y2:
                        end_char = lower_corner
                    if y1 > y2:
                        end_char = upper_corner
                else:
                    end_char = line_hor
            se_count += 1
            se_status = _("E:left/right")

        # links und rechts -
        if self.cell(Pos(x2 - 1, y2)) == line_hor \
                and self.cell(Pos(x2 + 1, y2)) == line_hor:
            if (start_ori == VERTICAL and x1 == x2) or (start_ori == HORIZONTAL and y1 != y2):
                end_char = connect_char
            se_count += 1
            se_status = _("E:left and right {}").format(line_hor)

        # links oder rechts - unten |
        if (self.cell(Pos(x2 - 1, y2)) == line_hor or self.cell(Pos(x2 + 1, y2)) == line_hor) \
                and self.cell(Pos(x2 + 1, y2)) == space_char \
                and self.cell(Pos(x2, y2 + 1)) == line_vert:
            end_char = connect_char
            se_count += 1
            se_status = _("E: l{0}/r{1} bottom={2}").format(upper_corner, lower_corner, line_vert)

        # generell, wenn endc noch # ist
        if end_char == '#':
            if start_ori == VERTICAL:
                if x1 == x2:
                    end_char = line_vert
                else:
                    end_char = line_hor
            if start_ori == HORIZONTAL:
                if y1 != y2:
                    end_char = line_vert
                else:
                    end_char = line_hor

        return se_count, se_status, end_char

    def _draw_line(self, startc, start_ori, endc):
        repr = dict()
        line_hor = Preferences.values['LINE_HOR']
        line_vert = Preferences.values['LINE_VERT']
        upper_corner = Preferences.values['UPPER_CORNER']
        lower_corner = Preferences.values['LOWER_CORNER']
        startpos = self._startpos
        endpos = self._endpos
        corner_char = '%'
        cornerpos = Pos(0, 0)

        if start_ori == VERTICAL:
            if endpos.y > startpos.y:
                corner_char = lower_corner
            else:
                corner_char = upper_corner
            mx = startpos.x
            if endpos.y > startpos.y:
                my = startpos.y + 1
                while my < endpos.y:
                    repr[Pos(mx, my)] = line_vert
                    my += 1
            if startpos.y > endpos.y:
                my = startpos.y - 1
                while my > endpos.y:
                    repr[Pos(mx, my)] = line_vert
                    my -= 1
            my = endpos.y
            if endpos.x > startpos.x:
                mx = startpos.x + 1
                while mx < endpos.x:
                    repr[Pos(mx, my)] = line_hor
                    mx += 1
            if startpos.x > endpos.x:
                mx = startpos.x - 1
                while mx > endpos.x:
                    repr[Pos(mx, my)] = line_hor
                    mx -= 1
            cornerpos = Pos(startpos.x, endpos.y)

        if start_ori == HORIZONTAL:
            if endpos.y < startpos.y:
                corner_char = lower_corner
            else:
                corner_char = upper_corner
            my = startpos.y
            if endpos.x > startpos.x:
                mx = startpos.x + 1
                while mx < endpos.x:
                    repr[Pos(mx, my)] = line_hor
                    mx += 1
            if startpos.x > endpos.x:
                mx = startpos.x - 1
                while mx > endpos.x:
                    repr[Pos(mx, my)] = line_hor
                    mx -= 1
            mx = endpos.x
            if endpos.y > startpos.y:
                my = startpos.y + 1
                while my < endpos.y:
                    repr[Pos(mx, my)] = line_vert
                    my += 1
            if startpos.y > endpos.y:
                my = startpos.y - 1
                while my > endpos.y:
                    repr[Pos(mx, my)] = line_vert
                    my -= 1
            cornerpos = Pos(endpos.x, startpos.y)

        repr[cornerpos] = corner_char
        repr[startpos] = startc
        repr[endpos] = endc
        self._repr = repr


class Rect(Symbol):

    def __init__(self, startpos, endpos):
        if startpos > endpos:
            tmp = endpos
            endpos = startpos
            startpos = tmp
        grid = {"N": ['?']}
        super(Rect, self).__init__(grid=grid, startpos=startpos, endpos=endpos)
        self._is_symbol = False
        self._is_line = True
        self._representation()

    def _representation(self):
        ul = self._startpos
        ur = Pos(self._endpos.x, self._startpos.y)
        bl = Pos(self._startpos.x, self._endpos.y)
        br = self._endpos
        line1 = Line(ul, ur, Line.LINE1)
        line2 = Line(ur, br, Line.LINE4)
        line3 = Line(bl, br, Line.LINE1)
        line4 = Line(ul, bl, Line.LINE4)
        self._repr = dict()
        self._repr.update(line1.repr)
        self._repr.update(line3.repr)
        self._repr.update(line2.repr)
        self._repr.update(line4.repr)

    def rotate(self):
        w = self._endpos.x - self._startpos.x
        h = self._endpos.y - self._startpos.y
        ul = self._startpos
        br = Pos(self._startpos.x + h, self._startpos.y + w)
        self._startpos = ul
        self._endpos = br

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        return Rect(startpos, endpos)

    def memo(self):
        str = "{0}:{1},{2}".format(DRAW_RECT, self._startpos, self._endpos)
        return str


class Arrow(Symbol):

    def __init__(self, startpos, endpos):
        grid = {"N": ['?']}
        super(Arrow, self).__init__(grid=grid, startpos=startpos, endpos=endpos)
        self._is_symbol = False
        self._is_line = True
        self._representation()

    def _direction(self):
        dx = abs(self._endpos.x - self._startpos.x)
        dy = abs(self._endpos.y - self._startpos.y)
        if dx > dy:
            return HORIZONTAL
        else:
            return VERTICAL

    def _representation(self):
        if self._direction() == HORIZONTAL:
            self._repr_hor()
        else:
            self._repr_vert()

    def _repr_hor(self):
        startpos = self._startpos
        endpos = self._endpos
        h = startpos.y - endpos.y
        if h == 0:
            h = 3
        h = h - h % 3
        h2 = h / 2
        h3 = h / 3
        my = (startpos.y + endpos.y) / 2
        a = Pos(startpos.x, startpos.y - h3)
        b = Pos(startpos.x, endpos.y + h3)
        c = Pos(endpos.x - h2, endpos.y + h3)
        d = Pos(endpos.x - h2, endpos.y)
        e = Pos(endpos.x, my)
        f = Pos(endpos.x - h2, startpos.y)
        g = Pos(endpos.x - h2, startpos.y - h3)
        self._repr_poly(a, b, c, d, e, f, g)
        self._pickpoint = c

    def _repr_vert(self):
        startpos = self._startpos
        endpos = self._endpos
        w = endpos.x - startpos.x
        if w == 0:
            w = 3
        w = w - w % 3
        w2 = w / 2
        w3 = w / 3
        mx = (startpos.x + endpos.x) / 2
        a = Pos(endpos.x - w3, startpos.y)
        b = Pos(startpos.x + w3, startpos.y)
        c = Pos(startpos.x + w3, endpos.y + w2)
        d = Pos(startpos.x, endpos.y + w2)
        e = Pos(mx, endpos.y)
        f = Pos(endpos.x, endpos.y + w2)
        g = Pos(endpos.x - w3, endpos.y + w2)
        self._repr_poly(a, b, c, d, e, f, g)
        self._pickpoint = c

    def _repr_poly(self, a, b, c, d, e, f, g):
        line1 = Line(a, b, Line.LINE4)
        line2 = Line(b, c, Line.LINE4)
        line3 = Line(c, d, Line.LINE1)
        line4 = DirLine(d, e)
        line5 = DirLine(e, f)
        line6 = Line(f, g, Line.LINE1)
        line7 = Line(g, a, Line.LINE4)
        self._repr = dict()
        # TODO more or less optimal order for horizontal arrow pointing to the right, what with the other ones?
        self._repr.update(line1.repr)
        self._repr.update(line3.repr)
        self._repr.update(line4.repr)
        self._repr.update(line6.repr)
        self._repr.update(line5.repr)
        self._repr.update(line7.repr)
        self._repr.update(line2.repr)

    @property
    def pickpoint_pos(self):
        return self._pickpoint

    def copy(self):
        startpos = copy.deepcopy(self._startpos)
        endpos = copy.deepcopy(self._endpos)
        return Arrow(startpos, endpos)

    def memo(self):
        str = "{0}:{1},{2}".format(ARROW, self._startpos, self._endpos)
        return str


class Column(Symbol):

    def __init__(self, col, action):
        super(Column, self).__init__(id=col, startpos=Pos(col, 0))
        self._col = col
        self._action = action
        self._is_symbol = False
        self._has_pickpoint = False

    @property
    def col(self):
        return self._col

    def paste(self, grid):
        if self._action == INSERT:
            grid.insert_col(self.col)
        else:
            grid.remove_col(self.col)

    def remove(self, grid):
        """Revert the action."""
        if self._action == INSERT:
            grid.remove_col(self.col)
        else:
            grid.insert_col(self.col)

    def memo(self):
        if self._action == INSERT:
            str = "i"
        else:
            str = "d"
        str += "{0}:{1}".format(COL, self.col)
        return str

    def copy(self):
        return Column(self._col, self._action)


class Row(Symbol):

    def __init__(self, row, action):
        super(Row, self).__init__(id=row, startpos=Pos(0, row))
        self._row = row
        self._action = action
        self._is_symbol = False
        self._has_pickpoint = False

    @property
    def row(self):
        return self._row

    def paste(self, grid):
        if self._action == INSERT:
            grid.insert_row(self.row)
        else:
            grid.remove_row(self.row)

    def remove(self, grid):
        """Revert the action."""
        if self._action == INSERT:
            grid.remove_row(self.row)
        else:
            grid.insert_row(self.row)

    def memo(self):
        if self._action == INSERT:
            str = "i"
        else:
            str = "d"
        str += "{0}:{1}".format(ROW, self.row)
        return str

    def copy(self):
        return Row(self._row, self._action)
