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
from yaml.loader import ConstructorError
import os.path


def configure(var_map):
    def join(loader, node):
        """
        YAML Tag handler to join components to a string
        :param loader: YAML Loader
        :param node: Node, can be sequence or space-separated scalars
        :return: The components of node, will be joined together
        """
        try:
            seq = loader.construct_sequence(node)
            return ''.join([str(i) for i in seq])
        except ConstructorError as e:
            s = loader.construct_scalar(node)
            return ''.join(s.split())


    def interpret_var(loader, node):
        """
        YAML Tag handler to replace variables
        :param loader: YAML Loader
        :param node: Node, must be scalar
        :return: The value from the 'vars' dict above matching the key represented by node
        """
        key = loader.construct_scalar(node)
        return var_map[key]


    def change_ext(loader, node):
        """
        YAML Tag handler to change extension of a file
        :param loader: YAML Loader
        :param node: Node, can be sequence or space-separated scalars. filename and new extension
        :return: A file path, with the extension replaced
        """
        try:
            seq = loader.construct_sequence(node)
        except ConstructorError as e:
            seq = loader.construct_scalar(node).split()
        seq[0] = os.path.splitext(seq[0])[0]
        return '.'.join(seq)

    def base(loader, node):
        """
        YAML Tag handler to get base name of a file
        :param loader: YAML Loader
        :param node: Node, can be sequence or scalar. File name in full path
        :return: The file name from a path
        """
        try:
            seq = loader.construct_sequence(node)
        except ConstructorError as e:
            seq = loader.construct_scalar(node).split()
        path = seq[0]
        return os.path.basename(path)

    # Register tag handlers
    yaml.add_constructor('!join', join)
    yaml.add_constructor('!var', interpret_var)
    yaml.add_constructor('!change_ext', change_ext)
    yaml.add_constructor('!base', base)
