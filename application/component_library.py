"""
component_library.py

2020-03-02 JvO
"""

import json
import locale
from pubsub import pub
from pathlib import Path
from collections import OrderedDict

from application import gettext as _
from application import ERROR
from application import get_path_to_data
from application.symbol import Symbol


class ComponentLibrary(object):

    ORIENTATION = ('N', 'E', 'S', 'W')

    def __init__(self):
        self._libraries = []

        default_lib = 'component_en.json'
        default_lang, coding = locale.getdefaultlocale()
        if default_lang:
            lang = default_lang[:2]
            lib = 'component_' + lang + '.json'
            lib_path = get_path_to_data('components/' + lib)
            check = Path(lib_path)
            if check.is_file():
                self._libraries.append(lib)
            else:
                self._libraries.append(default_lib)
        else:
            self._libraries.append(default_lib)

        # optional user libraries
        for n in range(5):
            user_lib = ("user_component_{0}.json".format(n + 1))
            check = Path(get_path_to_data('components/' + user_lib))
            if check.is_file():
                self._libraries.append(user_lib)

        self._components = {}
        for lib in self._libraries:
            try:
                f = open(get_path_to_data('components/' + lib), "r")
                self._components.update(json.load(f))
                f.close()
            except IOError as e:
                msg = _("Failed to load component library {0} due to I/O error {1}: {2}").format(lib, e.errno, e.strerror)
                pub.sendMessage('STATUS_MESSAGE', msg=msg, type=ERROR)
                print(msg)

        # check component id's
        if len(self._components) > 0:
            ids = set()
            for label, symbol in self._components.items():
                id = symbol['id']
                if id in ids:
                    msg = _("Symbol: {} has duplicate id: {} !").format(label, id)
                    pub.sendMessage('STATUS_MESSAGE', msg=msg, type=ERROR)
                else:
                    ids.add(id)
        # order by id
        self._components = OrderedDict(sorted(self._components.items(), key=lambda t: t[1]['id']))

        self._key = None
        self._dir = None

    @property
    def components(self):
        return self._components

    def get_id(self, key):
        """
        return the symbol identifier for the given component name.

        :param key: the component name
        :returns the symbol id
        """
        if len(key) == 1:
            # single character id is its (decimal) ASCII value
            id = ord(key)
        else:
            id = self._components[key]['id']

        return id

    def get_grid(self, key):
        """
        return the grid for the symbol that represents the given component.

        :param key: the component name
        :return the symbol grid
        """
        self._key = key

        if len(key) == 1:
            # the single character grid is simply the character itself
            grid = [[key]]
        else:
            grid = self._components[key]['grid']

        return grid

    def get_symbol(self, key):
        """
        return the id and grid for the symbol that represents the given component.

        :param key: the component name
        :returns the symbol
        """
        grid = self.get_grid(key)
        id = self.get_id(key)
        symbol = Symbol(id, grid)

        return symbol

    def get_symbol_byid(self, id):
        """
        Return the symbol having the given id.

        :param key: the component name
        :returns the symbol
        """
        found = None
        for label, symbol in self._components.items():
            if symbol['id'] == id:
                found = symbol['id']
                grid = symbol['grid']
                break

        if found:
            return Symbol(id=found, grid=grid)
        else:
            return Symbol()

    def nr_components(self):
        return len(self._components)

    def nr_libraries(self):
        return len(self._libraries)


if __name__ == '__main__':
    lib = ComponentLibrary()
    print(_("Number of libraries loaded: {0}").format(lib.nr_libraries()))
