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

import unittest
from models import Step
from utils import extract_var_map


class StepTestCase(unittest.TestCase):

    def setUp(self):
        self.name = 'Test Step'
        self.image = 'docker/image'
        self.infiles = {'INPUT_FILE_0': '/path/to/readonly0/input_file.ext',
                        'INPUT_FILE_1': '/path/to/readonly1/input_file'}
        self.outfiles = {'OUTPUT_FILE': '/path/to/readwrite/output_file.ext'}
        self.expected_binds = {
            '/path/to/readonly0': {'bind': '/mnt/input_0', 'ro': True},
            '/path/to/readonly1': {'bind': '/mnt/input_1', 'ro': True},
            '/path/to/readwrite': {'bind': '/mnt/output_0', 'ro': False}
        }
        self.expected_environment = {
            'INPUT_FILE_0': '/mnt/input_0/input_file.ext',
            'INPUT_FILE_1': '/mnt/input_1/input_file',
            'OUTPUT_FILE': '/mnt/output_0/output_file.ext'
        }
        self.expected_volumes = ['/mnt/input_0', '/mnt/input_1', '/mnt/output_0']

    def test_create_step(self):
        step = Step(self.name, self.image)
        self.assertIsNotNone(step)

    def test_create_requires_name_image(self):
        self.assertRaises(TypeError, Step)
        self.assertRaises(TypeError, Step, None)
        self.assertRaises(TypeError, Step, None, self.image)
        self.assertRaises(TypeError, Step, self.name, None)

    def test_binds(self):
        step = Step(self.name, self.image, infiles=self.infiles, outfiles=self.outfiles)
        self.assertIsNotNone(step.binds)
        self.assertEqual(step.binds, self.expected_binds)

    def test_environment(self):
        step = Step(self.name, self.image, infiles=self.infiles, outfiles=self.outfiles)
        self.assertIsNotNone(step.environment)
        self.assertEqual(step.environment, self.expected_environment)

    def test_volumes(self):
        step = Step(self.name, self.image, infiles=self.infiles, outfiles=self.outfiles)
        self.assertEqual(step.get_volumes(), self.expected_volumes)

    def test_extract_var_map(self):
        leftovers = ['FOO=bar', 'BAZ=bat']
        var_map = extract_var_map(leftovers)
        self.assertEqual(var_map, {'FOO': 'bar', 'BAZ': 'bat'})

if __name__ == '__main__':
    unittest.main()
