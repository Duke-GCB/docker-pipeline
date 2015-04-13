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


if __name__ == '__main__':
    unittest.main()
