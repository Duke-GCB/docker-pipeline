__author__ = 'dcl9'
import yaml
import unittest
from tag_handlers import configure


class TagHandlersTestCase(unittest.TestCase):
    def setUp(self):
        self.var_map = {'VAR1': 'val1', 'VAR2': 'val2'}
        configure(self.var_map)
        self.loaded = None

    def load(self, document):
        self.loaded = yaml.load(document)

    def expect(self, expected, message):
        self.assertEqual(expected, self.loaded, message)

    def test_var(self):
        """
        Test variable interpolation
        """
        self.load('k: !var VAR1')
        self.expect({'k': self.var_map['VAR1']}, 'Variable interpolation with !var failed')

    def test_join(self):
        """
        Test joining values
        """
        self.load('k: !join [foo, bar]')
        self.expect({'k': 'foobar'}, 'Join Values with !join failed')

    def test_change_ext(self):
        """
        Test changing file extension
        """
        self.load('k: !change_ext foo.bar baz')
        self.expect({'k': 'foo.baz'}, 'Changing file extension with !change_ext failed')

    def test_base(self):
        """
        Test getting base name of file
        """
        self.load('k: !base /path/to/bar')
        self.expect({'k': 'bar'}, 'Getting basename with !base failed')

    def test_join_and_var(self):
        """
        Test join and var
        """
        self.load('k: !join [!var VAR1, !var VAR2]')
        self.expect({'k': 'val1val2'}, 'Combining !join and !var')

    def test_change_ext_and_base(self):
        """
        Test change_ext and base
        """
        self.load('k: !change_ext [!base /path/to/file.abc, def]')
        self.expect({'k': 'file.def'}, 'Combining !change_ext and !base')

if __name__ == '__main__':
    unittest.main()
