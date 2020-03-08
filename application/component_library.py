"""
component_library.py

2020-03-02 JvO
"""

import os
import sys


class ComponentLibrary(object):

    def __init__(self):

        self.libraries = []
        for n in range(4):
            self.libraries.append("component{0}.ini".format(n + 1))

        lib_path = os.path.dirname(__file__)
        print("Path: {0}".format(lib_path))

        self.components = []
        for lib in self.libraries:
            try:
                f = open(os.path.join(lib_path + "/components/", lib), "r")
                self.components.append(f.read(1))
                f.close()
            except IOError as e:
                print("Failed to load component library {0} due to I/O error {1}: {2}".format(lib, e.errno, e.strerror))
                sys.exit(1)

    def nr_libraries(self):
        return len(self.libraries)


if __name__ == "__main__":
    lib = ComponentLibrary()
    print("Number of libraries loaded: {0}".format(lib.nr_libraries()))
