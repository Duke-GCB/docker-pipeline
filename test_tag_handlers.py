#!/usr/bin/env python
#
# docker-pipeline
# 
# The MIT License (MIT)
# 
# Copyright (c) 2015 Dan Leehr
# 
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
# 
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
# 
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

__author__ = 'dcl9'

import yaml
import unittest
from tag_handlers import configure


class TagHandlersTestCase(unittest.TestCase):
    def setUp(self):
        self.var_map = {'VAR1': 'val1', 'VAR2': 'val2', 'FILE1': '/data/file.raw'}
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
        self.expect({'k': 'val1'}, 'Variable interpolation with !var failed')

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
        self.load('k: !join [!var FILE1, .zip]')
        self.expect({'k': '/data/file.raw.zip'}, 'Combining !join and !var')

    def test_change_ext_and_base(self):
        """
        Test change_ext and base
        """
        self.load('k: !change_ext [!base /path/to/file.abc, def]')
        self.expect({'k': 'file.def'}, 'Combining !change_ext and !base')

    def test_all(self):
        """
        Test all tags
        """
        self.load('k: !join [a,/,!var VAR2,/, !base [!change_ext [!var FILE1, new]]]')
        self.expect({'k': 'a/val2/file.new'}, 'Combining all tags')
if __name__ == '__main__':
    unittest.main()
