""" Test of desim API

:Author: Jonathan Karr <karr@mssm.edu>
:Date: 2019-01-20
:Copyright: 2019, Karr Lab
:License: MIT
"""

import desim
import re
import unittest


class ApiTestCase(unittest.TestCase):

    def test(self):
        self.assertRegex(desim.__version__, r'^[0-9]+\.[0-9]+\.[0-9]+[a-zA-Z0-9]*$')
