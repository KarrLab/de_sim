""" Test of de_sim API

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2019-01-20
:Copyright: 2019-2020, Karr Lab
:License: MIT
"""

import de_sim
import unittest


class ApiTestCase(unittest.TestCase):

    def test(self):
        self.assertRegex(de_sim.__version__, r'^[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9]*$')
