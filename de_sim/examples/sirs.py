""" Example DE-Sim implementations of a stochastic Susceptible, Infectious, or Recovered (SIR) epidemic model

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-07-08
:Copyright: 2020, Karr Lab
:License: MIT
"""

import enum
import numpy

from de_sim.event import Event
from de_sim.simulation_engine import SimulationEngine
from de_sim.simulation_message import SimulationMessage
from de_sim.simulation_object import ApplicationSimulationObject


class SusceptibleToInfectious(SimulationMessage):
    "S -> I transition"


class InfectiousToRecovered(SimulationMessage):
    "I -> R transition"


class RecordTrajectory(SimulationMessage):
    "Record trajectory"


MESSAGE_TYPES = [SusceptibleToInfectious, InfectiousToRecovered, RecordTrajectory]


class SIR(ApplicationSimulationObject):
    """ Implement a Susceptible, Infectious, or Recovered (SIR) epidemic model

    This example uses DE-Sim to implement a continuous-time Markov chain (CTMC) SIR
    epidemic model, as described in section 3 of Allen (2017).

    Allen, L.J., 2017. A primer on stochastic epidemic models: Formulation, numerical simulation, and analysis.
    Infectious Disease Modelling, 2(2), pp.128-142.

    Attributes:
        s (:obj:`int`): initial number of susceptible subjects, s(0)
        i (:obj:`int`): initial number of infectious subjects, i(0)
        N (:obj:`int`): total number of susceptible subjects, a constant
        beta (:obj:`float`): SIR beta parameter
        gamma (:obj:`float`): SIR gamma parameter
        state_period (:obj:`float`): time step for recording state
        random_state (:obj:`numpy.random.RandomState`): random state
        history (:obj:`list`): list of recorded states
    """
    def __init__(self, name, s, i, N, beta, gamma, state_period):
        self.s = s
        self.i = i
        self.N = N
        self.beta = beta
        self.gamma = gamma
        self.state_period = state_period
        self.random_state = numpy.random.RandomState()
        self.history = []
        super().__init__(name)

    def send_initial_events(self):
        """ Send the initial events, and record the initial state
        """
        self.schedule_next_event()
        self.record_trajectory(None)

    def schedule_next_event(self):
        """ Schedule the next SIR event
        """
        rates = {'s_to_i': self.beta * self.s * self.i / self.N,
                 'i_to_r': self.gamma * self.i}
        lambda_val = rates['s_to_i'] + rates['i_to_r']
        if lambda_val == 0:
            return

        tau = self.random_state.exponential(1.0/lambda_val)
        prob_s_to_i = rates['s_to_i'] / lambda_val
        if self.random_state.random_sample() < prob_s_to_i:
            self.send_event(tau, self, SusceptibleToInfectious())
        else:
            self.send_event(tau, self, InfectiousToRecovered())

    def handle_s_to_i(self, event):
        """ Handle a susceptible to infectious event

        Args:
            event (:obj:`Event`): simulation event; not used
        """
        self.s -= 1
        self.i += 1
        self.schedule_next_event()

    def handle_i_to_r(self, event):
        """ Handle an infectious to recovered event

        Args:
            event (:obj:`Event`): simulation event; not used
        """
        self.i -= 1
        self.schedule_next_event()

    def record_trajectory(self, event):
        """ Add another record to the SIR history

        Args:
            event (:obj:`Event`): simulation event; not used
        """
        self.history.append(dict(time=self.time,
                                 s=self.s,
                                 i=self.i))
        self.send_event(self.state_period, self, RecordTrajectory())

    event_handlers = [(SusceptibleToInfectious, 'handle_s_to_i'),
                      (InfectiousToRecovered, 'handle_i_to_r'),
                      (RecordTrajectory, 'record_trajectory')]

    # register the message types sent
    messages_sent = MESSAGE_TYPES


class StateTransition(SimulationMessage):
    "State transition"
    attributes = ['transition']


MESSAGE_TYPES = [StateTransition, RecordTrajectory]


class Transition(enum.Enum):
    """ Transition values
    """
    s_to_i = enum.auto()
    i_to_r = enum.auto()


class SIR2(SIR):
    """ Version 2 of a SIR epidemic model

    SIR2 is similar to SIR, but uses a event message type for both transitions, and a
    single message handler to process transition messages.
    """
    def schedule_next_event(self):
        """ Schedule the next SIR event
        """
        rates = {'s_to_i': self.beta * self.s * self.i / self.N,
                 'i_to_r': self.gamma * self.i}
        lambda_val = rates['s_to_i'] + rates['i_to_r']
        if lambda_val == 0:
            return

        tau = self.random_state.exponential(1.0/lambda_val)
        prob_s_to_i = rates['s_to_i'] / lambda_val
        if self.random_state.random_sample() < prob_s_to_i:
            self.send_event(tau, self, StateTransition(Transition.s_to_i))
        else:
            self.send_event(tau, self, StateTransition(Transition.i_to_r))

    def handle_state_transition(self, event):
        """ Handle an infectious transition

        Args:
            event (:obj:`Event`): simulation event that contains the type of transition
        """
        transition = event.message.transition
        if transition is Transition.s_to_i:
            self.s -= 1
            self.i += 1
        elif transition is Transition.i_to_r:
            self.i -= 1
        self.schedule_next_event()

    def record_trajectory(self, event):
        """ Add another record to the SIR history

        Args:
            event (:obj:`Event`): simulation event; not used
        """
        self.history.append(dict(time=self.time,
                                 s=self.s,
                                 i=self.i))
        self.send_event(self.state_period, self, RecordTrajectory())

    event_handlers = [(StateTransition, 'handle_state_transition'),
                      (RecordTrajectory, 'record_trajectory')]

    # register the message types sent
    messages_sent = MESSAGE_TYPES


class RunSIRs(object):

    @staticmethod
    def main(sir_class, time_max, seed, **sir_args):

        # create a simulator
        simulator = SimulationEngine()

        # create a SIR instance
        sir = sir_class(**sir_args)
        simulator.add_object(sir)

        # initialize simulation, which sends the SIR instance an initial event message
        simulator.initialize()

        # run the simulation
        event_num = simulator.simulate(time_max).num_events
        print("Executed {} events.\n".format(event_num))
        return sir

    @staticmethod
    def print_history(sir):
        header = ['time', 's', 'i', 'r']
        print('\t'.join(header))
        for state in sir.history:
            state_as_list = [state['time'], state['s'], state['i'], sir.N - state['s'] - state['i']]
            state_as_list = [str(v) for v in state_as_list]
            print('\t'.join(state_as_list))
