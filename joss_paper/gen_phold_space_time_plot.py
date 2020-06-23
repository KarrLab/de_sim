""" Generate a space-time plot of PHOLD

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-22
:Copyright: 2020, Karr Lab
:License: MIT
"""

from argparse import Namespace
import matplotlib.pyplot as plt
import numpy as np

from de_sim.examples.phold import RunPhold

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

# plotting parameters
plot_params = dict(
    width=1.0,
    time_axis_width=3,
    obj_name_font_size=8,
    event_line_width=2,
    event_dot_diam=4,
    msg_width=3,
    msg_arrow_width=6,
    msg_to_self_color='blue',
    msg_to_other_color='purple',
    msg_to_self_curve=30,
)

def plot_run():
    # get plot filename from config
    # read plot file
    
    ### generate space-time diagram
    # plot time axis
    fig, ax = plt.subplots()
    ax.spines['top'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['bottom'].set_visible(False)
    # ax.spines['left'].set_visible(False)
    ax.get_xaxis().set_ticks([])
    plt.gca().invert_yaxis()

    ax.arrow(0, 0, 0.5, 0.5, head_width=0.05, head_length=0.1, fc='k', ec='k')
    fig.savefig("test.png")
    plt.show()
    # write PHOLD object names
    # plot PHOLD event lines
    # plot PHOLD event dots
    # plot MessageSentToSelf messages
    # plot MessageSentToOtherObject messages
    # plot legend
    pass

def prepare_plot():
    # turn on plot logging through config
    # run_phold(10)
    plot_run()

prepare_plot()

'''
plt.plot([1, 2, 3, 4])
plt.ylabel('some numbers')
plt.show()
'''