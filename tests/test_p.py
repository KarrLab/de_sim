""" Test utilities

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-26
:Copyright: 2018, Karr Lab
:License: MIT
"""
import unittest
from progress.bar import IncrementalBar, Bar
from sys import stderr
from capturer import CaptureOutput


class TestUtilities1(unittest.TestCase):

    def test(self):
        print(stderr.isatty())

class TestUtilities2(unittest.TestCase):

    def test(self):
        bar = IncrementalBar('Simulating', max=10)
        bar.goto(5)
        bar.finish()

class TestUtilities3(unittest.TestCase):

    def test_raw_progress_1(self):
        bar = IncrementalBar('Simulating', max=10)
        bar.goto(5)
        bar.finish()

class TestUtilities4(unittest.TestCase):

    def test_raw_progress_2(self):
        with CaptureOutput(relay=False) as capturer:
            bar = IncrementalBar('Simulating', max=10)
            bar.goto(5)
            bar.finish()

class TestUtilities5(unittest.TestCase):

    def test_raw_progress_3(self):
        bar = Bar('Simulating', max=10)
        bar.goto(5)
        bar.finish()

class TestUtilities6(unittest.TestCase):

    def test_raw_progress_4(self):
        with CaptureOutput(relay=False) as capturer:
            bar = Bar('Simulating', max=10)
            bar.goto(5)
            bar.finish()
