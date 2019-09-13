""" Test utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-26
:Copyright: 2018, Karr Lab
:License: MIT
"""
import unittest
import sys
from abc import ABCMeta, abstractmethod
from capturer import CaptureOutput

from de_sim.utilities import ConcreteABCMeta, SimulationProgressBar


class AbstractBase(object, metaclass=ABCMeta):

    @abstractmethod
    def f(self):
        raise NotImplemented

    @abstractmethod
    def g(self):
        raise NotImplemented


class YourMeta(type):
    def __new__(cls, *args, **kwargs):
        newcls = super().__new__(cls, *args, **kwargs)
        return newcls


class CombinedMeta(ConcreteABCMeta, YourMeta): pass


class TestUtilities(unittest.TestCase):

    def test(self):
        with self.assertRaises(TypeError) as context:
            class ConcreteClass(AbstractBase, metaclass=CombinedMeta): pass
        self.assertIn("ConcreteClass has not implemented abstract methods", str(context.exception))

    def test_progress(self):
        unused_bar = SimulationProgressBar()
        self.assertEqual(unused_bar.start(1), None)
        self.assertEqual(unused_bar.progress(2), None)
        self.assertEqual(unused_bar.end(), None)

        used_bar = SimulationProgressBar(True)
        with CaptureOutput(relay=True) as capturer:
            try:
                duration = 20
                # open sys.stderr to workaround problem with karr_lab_build_utils run-tests closing it
                # and progressbar expecting it to remain open
                print('', file=sys.stderr)
                self.assertEqual(used_bar.start(duration), None)
                self.assertEqual(used_bar.progress(10), None)
                self.assertEqual(used_bar.progress(20), None)
                self.assertEqual(used_bar.end(), None)
                self.assertTrue("/{}".format(duration) in capturer.get_text())
                self.assertTrue("end_time".format(duration) in capturer.get_text())

            except ValueError as e:
                raise ValueError(e)
                if str(e) == 'I/O operation on closed file':
                    print("SimulationProgressBar failed because stderr was closed", file=sys.stderr)
                    print("See de_sim issue #18", file=sys.stderr)
                else:
                    self.fail('test_progress failed for unknown reason')
