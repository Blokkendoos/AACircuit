import os
import unittest

# from flake8.engine import get_style_guide
# flake8.api.legacy.get_style_guide(**kwargs)
# http://flake8.pycqa.org/en/latest/user/python-api.html

# import flake8.api.legacy
# def get_style_guide(*args, **kwargs):
#     return flake8.api.legacy.get_style_guide(*args, **kwargs)

from flake8.api import legacy as flake8

# disbale the flake8 logger:
# http://flake8.pycqa.org/en/latest/user/python-api.html
from logging import getLogger

getLogger('flake8').propagate = False

style_guide = flake8.get_style_guide(
    ignore=(
        'E129',  # visually indented line with same indent (in gui.py)
        'E501',  # line too long
        'E126',  # continuation line over-indented for hanging indent
        'E128',  # continuation line under-indented for visual indent
        # 'E221',  # multiple spaces before operator
        # 'E222',  # multiple spaces after operator
        'E722',  # do not use bare except
        'F403',  # 'import *' used; unable to detect undefined names
        'F405',  # ... may be undefined, or defined from star imports: ...
    ),
    report=None,
    exclude=[]
)


def base_directory():
    current = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(current, '..')


class Flake8Test(unittest.TestCase):

    def test_flake8(self):
        report = style_guide.check_files([
            base_directory()
        ])

        self.assertEqual(report.get_statistics('E'), [], 'Flake8 reports errors')
