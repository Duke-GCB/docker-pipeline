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

    # Register tag handlers
    yaml.add_constructor('!join', join)
    yaml.add_constructor('!var', interpret_var)
    yaml.add_constructor('!change_ext', change_ext)
