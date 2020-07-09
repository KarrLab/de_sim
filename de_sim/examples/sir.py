""" A stochastic Susceptible, Infectious, or Recovered (SIR) epidemic model


:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-07-08
:Copyright: 2020, Karr Lab
:License: MIT
"""

import argparse
import numpy
import math

from de_sim.simulation_engine import SimulationEngine
from de_sim.simulation_message import SimulationMessage
from de_sim.simulation_object import ApplicationSimulationObject


class SusceptibleToInfectious(SimulationMessage):
    "S -> I transition"


class InfectiousToRecovered(SimulationMessage):
    "I -> R transition"


class OutputState(SimulationMessage):
    "Output state"


MESSAGE_TYPES = [SusceptibleToInfectious, InfectiousToRecovered, OutputState]


class SIR(ApplicationSimulationObject):

    def __init__(self, name, s, i, N, beta, gamma, state_period):
        self.s = s
        self.i = i
        self.N = N
        self.beta = beta
        self.gamma = gamma
        self.state_period = state_period
        self.random_state = numpy.random.RandomState()
        super().__init__(name)

    def send_initial_events(self):
        self.schedule_next_event()
        self.output_state(None)

    def schedule_next_event(self):
        rates = {'s_to_i': self.beta * self.s * self.i / self.N,
                 'i_to_r': self.gamma * self.i}
        lambda_val = rates['s_to_i'] + rates['i_to_r']
        if lambda_val == 0:
            self.send_event(float('inf'), self, SusceptibleToInfectious())
            return
        tau = self.random_state.exponential(1.0/lambda_val)
        prob_s_to_i = rates['s_to_i'] / lambda_val
        if self.random_state.random_sample() < prob_s_to_i:
            self.send_event(tau, self, SusceptibleToInfectious())
        else:
            self.send_event(tau, self, InfectiousToRecovered())

    def handle_s_to_i(self, event):
        self.s -= 1
        self.i += 1
        self.schedule_next_event()

    def handle_i_to_r(self, event):
        self.i -= 1
        self.schedule_next_event()

    def output_state(self, event):
        if self.time == 0:
            header = ['time', 's', 'i', 'r']
            print('\t'.join(header))

        state = [self.time, self.s, self.i, self.N - self.s - self.i]
        state = [str(v) for v in state]
        print('\t'.join(state))
        self.send_event(self.state_period, self, OutputState())

    event_handlers = [(SusceptibleToInfectious, 'handle_s_to_i'),
                      (InfectiousToRecovered, 'handle_i_to_r'),
                      (OutputState, 'output_state')]

    # register the message types sent
    messages_sent = MESSAGE_TYPES


class RunSIR(object):

    @staticmethod
    def main(time_max, seed, **sir_args):

        # create a simulator
        simulator = SimulationEngine()

        # create SIR instance
        sir = SIR(**sir_args)
        simulator.add_object(sir)

        # initialize simulation which sends the sir instance an initial event message
        simulator.initialize()

        # run the simulation
        event_num = simulator.simulate(time_max).num_events
        print("Executed {} events.\n".format(event_num))
        return(event_num)

from argparse import Namespace

def run_sir():
    sir_args = dict(name='sir',
                    s=98,
                    i=2,
                    N=100,
                    beta=0.3,
                    gamma=0.15,
                    state_period=10)
    RunSIR.main(time_max=60, seed=17, **sir_args)

run_sir()

'''
if __name__ == '__main__':  # pragma: no cover     # reachable only from command line
    try:
        args = RunSIR.parse_args(sys.argv[1:])
        RunSIR.main(args)
    except KeyboardInterrupt:
        pass
'''
