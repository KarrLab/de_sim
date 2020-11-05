"""
:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-08-28
:Copyright: 2020, Karr Lab
:License: MIT
"""

import subprocess
import unittest


class TestPlotLog(unittest.TestCase):

    def test(self):
        # this tests two things:
        # 1) gen_phold_space_time_plot.py
        # 2) the use of self.fast_plot_file_logger in de_sim/de_sim/simulation_object.py, which cannot
        # be conveniently unit-tested because doing so requires that config state be changed before
        # de_sim.plot.file logger is created. This runs gen_phold_space_time_plot.py in a separate process
        # to execute that code.
        # also see the comment in LoggerConfigurator().from_dict() regarding shared loggers.
        try:
            command = ["python3", "joss_paper/figures/gen_phold_space_time_plot.py"]
            result = subprocess.run(command,
                                    check=True,
                                    capture_output=True)
        except subprocess.CalledProcessError as e:
            e_msg = f"""'{" ".join(command)}' failed:\n{e.stderr.decode("utf-8")}"""
            self.fail(e_msg)

        self.assertIn('space-time diagram written', result.stdout.decode("utf-8"))
