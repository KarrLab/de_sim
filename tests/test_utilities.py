""" Test utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-26
:Copyright: 2018, Karr Lab
:License: MIT
"""
import unittest
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


from progress.bar import IncrementalBar, Bar
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
        with CaptureOutput(relay=False) as capturer:
            duration = 20
            self.assertEqual(used_bar.start(duration), None)
            self.assertEqual(used_bar.progress(10), None)
            self.assertEqual(used_bar.progress(20), None)
            self.assertEqual(used_bar.end(), None)
            self.assertTrue('Simulating' in capturer.get_text())
            self.assertTrue(str(duration) in capturer.get_text())
            self.assertTrue('end time' in capturer.get_text())

    def test_raw_progress_1(self):
        bar = IncrementalBar('Simulating', max=10)
        bar.goto(5)
        bar.finish()

    def test_raw_progress_2(self):
        with CaptureOutput(relay=False) as capturer:
            bar = IncrementalBar('Simulating', max=10)
            bar.goto(5)
            bar.finish()

    def test_raw_progress_3(self):
        bar = Bar('Simulating', max=10)
        bar.goto(5)
        bar.finish()

    def test_raw_progress_4(self):
        with CaptureOutput(relay=False) as capturer:
            bar = Bar('Simulating', max=10)
            bar.goto(5)
            bar.finish()
