""" Test SIR model
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-07-09
:Copyright: 2020, Karr Lab
:License: MIT
"""

import sys
import unittest
import random
import warnings
from capturer import CaptureOutput

from de_sim.examples.sir import RunSIR


class TestSIR(unittest.TestCase):
    """ Test SIR model with parameters in Allen (2017), figure 1.

    Allen, L.J., 2017. A primer on stochastic epidemic models: Formulation, numerical simulation, and analysis.
    Infectious Disease Modelling, 2(2), pp.128-142.
    """

    def setUp(self):
        warnings.simplefilter("ignore")

    def test_run_sir(self):
        with CaptureOutput(relay=False) as capturer:
            sir_args = dict(name='sir',
                            s=98,
                            i=2,
                            N=100,
                            beta=0.3,
                            gamma=0.15,
                            state_period=10)
            sir = RunSIR.main(time_max=60, seed=17, **sir_args)
            RunSIR.print_history(sir)
            expected_output_strings = ['time', '\ts\t', '60\t', 'Executed']
            for expected_output_string in expected_output_strings:
                self.assertIn(expected_output_string, capturer.get_text())

        with CaptureOutput(relay=False):
            # test lambda_val == 0
            sir_args['i'] = 0
            RunSIR.main(time_max=20, seed=13, **sir_args)

    def test_P_minor_outbreak(self):
        # Allen (2017) estimates P[minor outbreak] for the CTMC model implemented in SIR as 0.25
        ensemble_size = 50
        num_minor_outbreaks = 0
        with CaptureOutput(relay=False):
            for _ in range(ensemble_size):
                sir_args = dict(name='sir',
                                s=98,
                                i=2,
                                N=100,
                                beta=0.3,
                                gamma=0.15,
                                state_period=10)
                seed = random.randrange(1E6)
                time_max = 60
                sir = RunSIR.main(time_max=time_max, seed=seed, **sir_args)
                # consider an outbreak to be minor if no infections remain and fewer than 10 people were infected
                if sir.history[-1]['i'] == 0 and 90 < sir.history[-1]['s']:
                    num_minor_outbreaks += 1
        p_minor_outbreak = num_minor_outbreaks / ensemble_size
        expected_p_minor_outbreak = 0.25
        self.assertGreater(p_minor_outbreak, 0.8 * expected_p_minor_outbreak)
        self.assertLess(p_minor_outbreak, 1.25 * expected_p_minor_outbreak)
