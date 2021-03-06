import unittest

from application.preferences import Preferences


class PreferencesTest(unittest.TestCase):

    def test_get(self):
        self.assertEquals(Preferences.values['FONTSIZE'], 12)

    def test_set(self):
        Preferences.values['FONTSIZE'] = 14
        self.assertEquals(Preferences.values['FONTSIZE'], 14)

    def test_nr_settings(self):
        # 2020-05-28 number of settings in the preferences testfile: 18
        p = Preferences()
        self.assertEquals(p.nr_values(), 18)

    def test_has_value(self):
        p = Preferences()
        self.assertTrue(p.has_value('FONTSIZE'))
        self.assertFalse(p.has_value('ONBEKEND'))

    def test_preferences_file(self):
        p = Preferences(filename='tests/files/test_aacircuit.ini')

        # test integer
        self.assertEquals(p.values['FONTSIZE'], 12)

        # test boolean
        self.assertEquals(p.values['SELECTION_DRAG'], False)

        # test string
        self.assertEquals(p.values['LINE_HOR'], '-')
