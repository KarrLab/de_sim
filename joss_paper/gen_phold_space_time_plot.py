""" Generate a space-time plot of PHOLD

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-22
:Copyright: 2020, Karr Lab
:License: MIT
"""

from argparse import Namespace

from de_sim.examples.phold import RunPhold
from de_sim.visualize import EventCoordinates, EventMessage, SpaceTime

'''
plan
1 run phold, writing plotting log
2 draw ST diagram of run, reading data from log
3 output diagram: png OK, try svg
'''

def run_phold(time_max, frac_self_events=0.3, num_phold_procs=3, seed=17):
    args = Namespace(time_max=time_max, frac_self_events=frac_self_events,
                     num_phold_procs=num_phold_procs, seed=seed)
    print(RunPhold.main(args).num_events, 'events')


def prepare_plot():
    # turn on plot logging through config
    # run_phold(10)
    space_time = SpaceTime(sample_data)
    space_time.plot_data("test.pdf")

prepare_plot()
