# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from application import DEFAULT_COMPONENT_KEY
from application.component_library import ComponentLibrary


class ComponentLibraryTest(unittest.TestCase):

    def test_by_id(self):

        c = ComponentLibrary()
        id = 1
        symbol = c.get_symbol_byid(id=id)

        self.assertEquals(symbol.id, id)

    def test_default(self):

        c = ComponentLibrary()
        key = DEFAULT_COMPONENT_KEY
        symbol = c.get_symbol(key=key)

        self.assertEquals(symbol.id, 1)
