"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-17
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""

from argparse import Namespace
from capturer import CaptureOutput
from copy import copy
import random
import sys
import unittest
import warnings

from de_sim.examples.phold import RunPhold
from de_sim.testing.utilities_for_testing import make_args


class TestPhold(unittest.TestCase):

    def setUp(self):
        warnings.simplefilter("ignore")

    def run_phold(self, seed, max_time):
        args = Namespace(max_time=max_time, frac_self_events=0.3, num_phold_procs=10, seed=seed)
        random.seed(seed)
        with CaptureOutput(relay=False):
            return(RunPhold.main(args))

    def test_phold_reproducibility(self):
        num_events1 = self.run_phold(123, 10)
        num_events2 = self.run_phold(123, 10)
        self.assertEqual(num_events1, num_events2)

        num_events2 = self.run_phold(173, 10)
        self.assertNotEqual(num_events1, num_events2)

    def test_phold_parse_args(self):
        num_procs = 3
        frac_self = 0.2
        max_time = 25.0
        seed = 1234
        cl = "{} {} {}".format(num_procs, frac_self, max_time)
        args = RunPhold.parse_args(cli_args=cl.split())
        self.assertEqual(args.num_phold_procs, num_procs)
        self.assertEqual(args.frac_self_events, frac_self)
        self.assertEqual(args.max_time, max_time)
        cl = "{} {} {} --seed {}".format(num_procs, frac_self, max_time, seed)
        args = RunPhold.parse_args(cli_args=cl.split())
        self.assertEqual(args.seed, seed)

    required = ['num_phold_procs', 'frac_self_events', 'max_time']

    def test_phold_parse_args_errors(self):
        arguments = dict(
            num_phold_procs=2,
            frac_self_events=0.3,
            max_time=10,
        )

        args = make_args(arguments, self.required, [])
        # test parser error handling
        errors = dict(
            num_phold_procs=[-2, 0],
            frac_self_events=[-1, 1.1]
        )
        with CaptureOutput(relay=False):
            print('\n--- testing RunPhold.parse_args() error handling ---', file=sys.stderr)
            for arg, error_vals in errors.items():
                for error_val in error_vals:
                    arguments2 = copy(arguments)
                    arguments2[arg] = error_val
                    args = make_args(arguments2, self.required, [])
                    with self.assertRaises(SystemExit):
                        RunPhold.parse_args(args)
            print('--- done testing RunPhold.parse_args() error handling ---', file=sys.stderr)
