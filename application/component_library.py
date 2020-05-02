"""
component_library.py

2020-03-02 JvO
"""

import os
import sys
import json

from application import _
from application.symbol import Symbol


class ComponentLibrary(object):

    ORIENTATION = ('N', 'E', 'S', 'W')

    def __init__(self):

        self._libraries = []
        # for n in range(2):
        #     self._libraries.append("component{0}.json".format(n + 1))
        self._libraries.append('component_en.json')

        lib_path = os.path.dirname(__file__)
        print("Path: {0}".format(lib_path))

        self._dict = {}
        for lib in self._libraries:
            try:
                f = open(os.path.join(lib_path + '/components/', lib), "r")
                self._dict.update(json.load(f))
                f.close()
            except IOError as e:
                print(_("Failed to load component library {0} due to I/O error {1}: {2}").format(lib, e.errno, e.strerror))
                sys.exit(1)

        self._key = None
        self._dir = None

    # TODO not a property, unless you make up a better name (than dict())
    def get_dict(self):
        return self._dict

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
            id = self._dict[key]['id']

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
            grid = self._dict[key]['grid']

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
        for label, symbol in self._dict.items():
            if symbol['id'] == id:
                found = symbol['id']
                grid = symbol['grid']
                break

        if found:
            return Symbol(id=found, grid=grid)
        else:
            return Symbol()

    def nr_components(self):
        return len(self._dict)

    def nr_libraries(self):
        return len(self._libraries)


if __name__ == '__main__':
    lib = ComponentLibrary()
    print(_("Number of libraries loaded: {0}").format(lib.nr_libraries()))
