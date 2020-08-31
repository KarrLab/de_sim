""" Test SIR model

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-07-09
:Copyright: 2020, Karr Lab
:License: MIT
"""

from capturer import CaptureOutput
import random
import tempfile
import unittest
import warnings

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
            with tempfile.TemporaryDirectory() as tmpdirname:
                sir_args = dict(name='sir',
                                s=98,
                                i=2,
                                N=100,
                                beta=0.3,
                                gamma=0.15,
                                recording_period=10)
                run_sirs = RunSIRs(tmpdirname)
                run_sirs.simulate(sir_class, max_time=60, **sir_args)
                run_sirs.print_history()
                expected_output_strings = ['time', '\ts\t', '60.0\t', 'Executed']
                for expected_output_string in expected_output_strings:
                    self.assertIn(expected_output_string, capturer.get_text())

        with CaptureOutput(relay=False):
            with tempfile.TemporaryDirectory() as tmpdirname:
                # test lambda_val == 0
                sir_args['i'] = 0
                RunSIRs(tmpdirname).simulate(sir_class, max_time=20, **sir_args)

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
                with tempfile.TemporaryDirectory() as tmpdirname:
                    run_sirs = RunSIRs(tmpdirname)
                    run_sirs.simulate(sir_class, max_time=60, **sir_args)

                    # consider an outbreak to be minor if no infections remain and fewer than 10 people were infected
                    last_checkpoint_state = run_sirs.last_checkpoint().state
                    if last_checkpoint_state['i'] == 0 and 90 < last_checkpoint_state['s']:
                        num_minor_outbreaks += 1
        p_minor_outbreak = num_minor_outbreaks / ensemble_size
        expected_p_minor_outbreak = 0.25
        self.assertGreater(p_minor_outbreak, 0.5 * expected_p_minor_outbreak)
        self.assertLess(p_minor_outbreak, 2 * expected_p_minor_outbreak)

    def test_P_minor_outbreak(self):
        self.run_P_minor_outbreak_test(SIR)
        self.run_P_minor_outbreak_test(SIR2)
