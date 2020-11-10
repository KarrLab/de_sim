""" Test utilities for testing

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-11-09
:Copyright: 2020, Karr Lab
:License: MIT
"""

import os
import unittest

from de_sim.testing.utilities_for_testing import unset_env_var


class Test(unittest.TestCase):

    def test(self):
        os.environ['FOO'] = 'bar'
        self.assertEqual(os.environ['FOO'], 'bar')
        with unset_env_var('FOO'):
            self.assertNotIn('FOO', os.environ)
        self.assertEqual(os.environ['FOO'], 'bar')

        with unset_env_var('XXX'):
            self.assertNotIn('XXX', os.environ)
        self.assertNotIn('XXX', os.environ)
