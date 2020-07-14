""" Test SIR model

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-07-09
:Copyright: 2020, Karr Lab
:License: MIT
"""

import unittest
import random
import warnings
from capturer import CaptureOutput

from de_sim.examples.sirs import SIR, SIR2, RunSIRs


class TestSIRs(unittest.TestCase):
    """ Test SIR models using parameters from Fig. 1 of Allen (2017).

    Allen, L.J., 2017. A primer on stochastic epidemic models: Formulation, numerical simulation, and analysis.
    Infectious Disease Modelling, 2(2), pp.128-142.
    """

    def setUp(self):
        warnings.simplefilter("ignore")

    def run_sir_test(self, sir_class):
        with CaptureOutput(relay=False) as capturer:
            sir_args = dict(name='sir',
                            s=98,
                            i=2,
                            N=100,
                            beta=0.3,
                            gamma=0.15,
                            recording_period=10)
            sir = RunSIRs.main(sir_class, time_max=60, seed=17, **sir_args)
            RunSIRs.print_history(sir)
            expected_output_strings = ['time', '\ts\t', '60\t', 'Executed']
            for expected_output_string in expected_output_strings:
                self.assertIn(expected_output_string, capturer.get_text())

        with CaptureOutput(relay=False):
            # test lambda_val == 0
            sir_args['i'] = 0
            RunSIRs.main(sir_class, time_max=20, seed=13, **sir_args)

    def test_run_sir(self):
        self.run_sir_test(SIR)
        self.run_sir_test(SIR2)

    def run_P_minor_outbreak_test(self, sir_class):
        # Allen (2017) estimates P[minor outbreak] for the SIR model shown in Fig. 1 as 0.25
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
                                recording_period=10)
                seed = random.randrange(1E6)
                sir = RunSIRs.main(sir_class, time_max=60, seed=seed, **sir_args)
                # consider an outbreak to be minor if no infections remain and fewer than 10 people were infected
                if sir.history[-1]['i'] == 0 and 90 < sir.history[-1]['s']:
                    num_minor_outbreaks += 1
        p_minor_outbreak = num_minor_outbreaks / ensemble_size
        expected_p_minor_outbreak = 0.25
        self.assertGreater(p_minor_outbreak, 0.5 * expected_p_minor_outbreak)
        self.assertLess(p_minor_outbreak, 2 * expected_p_minor_outbreak)

    def test_P_minor_outbreak(self):
        self.run_P_minor_outbreak_test(SIR)
        self.run_P_minor_outbreak_test(SIR2)
