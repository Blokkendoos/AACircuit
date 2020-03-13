"""
component_library.py

2020-03-02 JvO
"""

import os
import sys
import json


class ComponentLibrary(object):

    def __init__(self):

        self._libraries = []
        for n in range(2):
            self._libraries.append("component{0}.json".format(n + 1))

        lib_path = os.path.dirname(__file__)
        print("Path: {0}".format(lib_path))

        self._dict = {}
        for lib in self._libraries:
            try:
                f = open(os.path.join(lib_path + "/components/", lib), "r")
                self._dict.update(json.load(f))
                f.close()
            except IOError as e:
                print("Failed to load component library {0} due to I/O error {1}: {2}".format(lib, e.errno, e.strerror))
                sys.exit(1)

    def get_dict(self):
        return self._dict

    def get_grid(self, key, dir="N"):
        """
        return the grid for the symbol that represents the given component.

        :param key: the component name
        :param dir: direction of the grid (N(orth, E(ast, S(outh, W(est)
        """
        return self._dict[key]["grid"][dir]

    def nr_components(self):
        return len(self._dict)

    def nr_libraries(self):
        return len(self._libraries)


if __name__ == "__main__":
    lib = ComponentLibrary()
    print("Number of libraries loaded: {0}".format(lib.nr_libraries()))
