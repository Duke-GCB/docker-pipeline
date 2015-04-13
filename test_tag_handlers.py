__author__ = 'dcl9'
import yaml
import unittest
from tag_handlers import configure


class TagHandlersTestCase(unittest.TestCase):
    def setUp(self):
        self.var_map = {'VAR1': 'val1', 'VAR2': 'val2'}
        configure(self.var_map)

    def load(self, document):
        self.loaded = yaml.load(document)

    def check(self, message):
        self.assertEqual(self.expected, self.loaded, message)

    def test_var(self):
        """
        Test variable interpolation
        """
        self.load('k: !var VAR1')
        self.expected = {'k': self.var_map['VAR1']}
        self.check('Variable interpolation with !var failed')

    def test_join(self):
        """
        Test joining values
        """
        self.load('k: !join [foo, bar]')
        self.expected = {'k': 'foobar'}
        self.check('Join Values with !join failed')

    def test_change_ext(self):
        """
        Test changing file extension
        """
        self.load('k: !change_ext foo.bar baz')
        self.expected = {'k': 'foo.baz'}
        self.check('Changing file extension with !change_ext failed')

    def test_base(self):
        """
        Test getting base name of file
        """
        self.load('k: !base /path/to/bar')
        self.expected = {'k': 'bar'}
        self.check('Getting basename with !base failed')

    def test_join_and_var(self):
        """
        Test join and var
        """
        self.load('k: !join [!var VAR1, !var VAR2]')
        self.expected = {'k': 'val1val2'}
        self.check('Combining !join and !var')

    def test_change_ext_and_base(self):
        """
        Test change_ext and base
        """
        self.load('k: !change_ext [!base /path/to/file.abc, def]')
        self.expected = {'k': 'file.def'}
        self.check('Combining !change_ext and !base')

if __name__ == '__main__':
    unittest.main()
