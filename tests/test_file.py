# NB to be run with nose, this .py should _not_ be executable (chmod -x)

import unittest

from pubsub import pub
from application.controller import Controller


class FileTest(unittest.TestCase):

    def test_read_write(self):

        c = Controller()

        filename = 'tests/files/test_all.aac'
        self.assertTrue(c.on_read_from_file(filename))

        filename = 'tests/files/temp.aac'
        self.assertTrue(c.on_write_to_file(filename))
