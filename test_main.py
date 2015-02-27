__author__ = 'dcl9'

import unittest
from main import Step

class StepTestCase(unittest.TestCase):

    def setUp(self):
        self.image = 'docker/image'
        self.infiles = {'INPUT_FILE_0': '/path/to/readonly0/input_file.ext', 'INPUT_FILE_1': '/path/to/readonly1/input_file'}
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
        step = Step(self.image)
        self.assertIsNotNone(step)

    def test_create_requires_image(self):
        self.assertRaises(TypeError, Step)
        self.assertRaises(TypeError, Step, None)

    def test_binds(self):
        step = Step(self.image, infiles=self.infiles, outfiles=self.outfiles)
        self.assertIsNotNone(step.binds)
        self.assertEqual(step.binds, self.expected_binds)

    def test_environment(self):
        step = Step(self.image, infiles=self.infiles, outfiles=self.outfiles)
        self.assertIsNotNone(step.environment)
        self.assertEqual(step.environment, self.expected_environment)

    def test_volumes(self):
        step = Step(self.image, infiles=self.infiles, outfiles=self.outfiles)
        self.assertEqual(step.get_volumes(), self.expected_volumes)


if __name__ == '__main__':
    unittest.main()
