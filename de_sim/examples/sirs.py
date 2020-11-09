""" Example DE-Sim implementations of stochastic Susceptible, Infectious, or Recovered (SIR) epidemic models

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-07-08
:Copyright: 2020, Karr Lab
:License: MIT
"""

import enum
import numpy

from de_sim.checkpoint import AccessCheckpoints
from de_sim.simulation_checkpoint_object import (AccessStateObjectInterface,
                                                 CheckpointSimulationObject)
import de_sim


class SusceptibleToInfectious(de_sim.EventMessage):
    "S -> I transition"


class InfectiousToRecovered(de_sim.EventMessage):
    "I -> R transition"


MESSAGE_TYPES = [SusceptibleToInfectious, InfectiousToRecovered]


class SIR(de_sim.SimulationObject):
    """ Implement a Susceptible, Infectious, or Recovered (SIR) epidemic model

    This example uses DE-Sim to implement a continuous-time Markov chain (CTMC) SIR
    epidemic model, as described in section 3 of Allen (2017).

    Allen, L.J., 2017. A primer on stochastic epidemic models: Formulation, numerical simulation, and analysis.
    Infectious Disease Modelling, 2(2), pp.128-142.

    Attributes:
        s (:obj:`int`): number of susceptible subjects
        i (:obj:`int`): number of infectious subjects
        N (:obj:`int`): total number of susceptible subjects, a constant
        beta (:obj:`float`): SIR beta parameter
        gamma (:obj:`float`): SIR gamma parameter
        recording_period (:obj:`float`): time step for recording state
        random_state (:obj:`numpy.random.RandomState`): a random state
        history (:obj:`list`): list of recorded states
    """
    def __init__(self, name, s, i, N, beta, gamma, recording_period):
        """ Initialize an SIR instance

        Args:
            name (:obj:`str`): the instance's name
            s (:obj:`int`): initial number of susceptible subjects, s(0)
            i (:obj:`int`): initial number of infectious subjects, i(0)
            N (:obj:`int`): total number of susceptible subjects, a constant
            beta (:obj:`float`): SIR beta parameter
            gamma (:obj:`float`): SIR gamma parameter
            recording_period (:obj:`float`): time step for recording state
            random_state (:obj:`numpy.random.RandomState`): random state
            history (:obj:`list`): list of recorded states
        """
        self.s = s
        self.i = i
        self.N = N
        self.beta = beta
        self.gamma = gamma
        self.recording_period = recording_period
        self.random_state = numpy.random.RandomState()
        self.history = []
        super().__init__(name)

    def init_before_run(self):
        """ Send the initial events, and record the initial state
        """
        self.schedule_next_event()

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
            event (:obj:`~de_sim.event.Event`): simulation event; not used
        """
        del event   # Avoid PyLint warning W0613, unused-argument
        self.s -= 1
        self.i += 1
        self.schedule_next_event()

    def handle_i_to_r(self, event):
        """ Handle an infectious to recovered event

        Args:
            event (:obj:`~de_sim.event.Event`): simulation event; not used
        """
        del event   # Avoid PyLint warning W0613, unused-argument
        self.i -= 1
        self.schedule_next_event()

    event_handlers = [(SusceptibleToInfectious, 'handle_s_to_i'),
                      (InfectiousToRecovered, 'handle_i_to_r')]

    # register the message types sent
    messages_sent = MESSAGE_TYPES


class StateTransitionType(enum.Enum):
    """ State transition types
    """
    s_to_i = 'Transition from Susceptible to Infectious'
    i_to_r = 'Transition from Infectious to Recovered'


### SIR epidemic model, version 2 ###
class TransitionMessage(de_sim.EventMessage):
    "Message for all model transitions"
    transition_type: StateTransitionType


MESSAGE_TYPES = [TransitionMessage]


class SIR2(SIR):
    """ Version 2 of an SIR epidemic model

    SIR2 is similar to SIR, but uses one event message type for both transitions, and a
    single message handler to process transition events.
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
            self.send_event(tau, self, TransitionMessage(StateTransitionType.s_to_i))
        else:
            self.send_event(tau, self, TransitionMessage(StateTransitionType.i_to_r))

    def handle_state_transition(self, event):
        """ Handle an infectious state transition

        Args:
            event (:obj:`~de_sim.event.Event`): simulation event that contains the type of transition
        """
        transition_type = event.message.transition_type
        if transition_type is StateTransitionType.s_to_i:
            self.s -= 1
            self.i += 1
        elif transition_type is StateTransitionType.i_to_r:
            self.i -= 1
        self.schedule_next_event()

    event_handlers = [(TransitionMessage, 'handle_state_transition')]

    # register the message types sent
    messages_sent = MESSAGE_TYPES


class AccessSIRObjectState(AccessStateObjectInterface):
    """ Get the state of an SIR object

    Attributes:
        sir (:obj:`obj`): an SIR object
        random_state (:obj:`numpy.random.RandomState`): a random state
    """

    def __init__(self, sir):
        self.sir = sir
        self.random_state = sir.random_state

    def get_checkpoint_state(self, time):
        """ Get the SIR object's state

        Args:
            time (:obj:`float`): current time; ignored
        """
        return dict(s=self.sir.s,
                    i=self.sir.i)

    def get_random_state(self):
        """ Get the SIR object's random state
        """
        return self.random_state.get_state()


class RunSIRs(object):

    def __init__(self, checkpoint_dir):
        self.checkpoint_dir = checkpoint_dir

    def simulate(self, sir_class, max_time, **sir_args):
        """ Create and run an SIR simulation

        Args:
            sir_class (:obj:`type`): a type of SIR class to run
            max_time (:obj:`float`): simulation end time
            sir_args (:obj:`dict`): arguments for an SIR object
        """

        # create a simulator
        simulator = de_sim.Simulator()

        # create an SIR instance
        self.sir = sir = sir_class(**sir_args)
        simulator.add_object(sir)

        # create a checkpoint simulation object
        access_state_object = AccessSIRObjectState(sir)
        checkpointing_obj = CheckpointSimulationObject('checkpointing_obj', sir_args['recording_period'],
                                                       self.checkpoint_dir, access_state_object)
        simulator.add_object(checkpointing_obj)

        # initialize simulation, which sends the SIR instance an initial event message
        simulator.initialize()

        # run the simulation
        event_num = simulator.simulate(max_time).num_events
        print("Executed {} events.\n".format(event_num))

    def print_history(self):
        """ Print an SIR simulation's history
        """
        header = ['time', 's', 'i', 'r']
        print('\t'.join(header))

        access_checkpoints = AccessCheckpoints(self.checkpoint_dir)
        for checkpoint_time in access_checkpoints.list_checkpoints():
            chkpt = access_checkpoints.get_checkpoint(time=checkpoint_time)
            state = chkpt.state
            state_as_list = [checkpoint_time, state['s'], state['i'], self.sir.N - state['s'] - state['i']]
            state_as_list = [str(v) for v in state_as_list]
            print('\t'.join(state_as_list))

    def last_checkpoint(self):
        """ Get the last checkpoint of the last simulation run

        Returns:
            :obj:`~de_sim.checkpoint.Checkpoint`: the last checkpoint of the last simulation run
        """
        access_checkpoints = AccessCheckpoints(self.checkpoint_dir)
        last_checkpoint_time = access_checkpoints.list_checkpoints()[-1]
        return access_checkpoints.get_checkpoint(time=last_checkpoint_time)
