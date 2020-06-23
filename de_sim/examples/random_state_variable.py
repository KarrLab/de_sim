""" A trivial simulation that increments or decrements a variable at each event

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-27
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""
import sys
import argparse
import random
from de_sim.simulation_message import SimulationMessage
from de_sim.simulation_object import ApplicationSimulationObject
from de_sim.simulation_engine import SimulationEngine


class MessageSentToSelf(SimulationMessage):
    "A message that's sent to self"


class RandomStateVariableSimulationObject(ApplicationSimulationObject):
    """ The random state variable model

    * State: a number
    * Event scheduling: schedule events randomly
    * Event execution: randomly increment or decrement the state
    """

    def __init__(self, name, initial_value, output=True):
        self.state = initial_value
        self.output = output
        super().__init__(name)

    def send_initial_events(self):
        self.send_event(0, self, MessageSentToSelf())
        self.send_event(1, self, MessageSentToSelf())

    def handle_simulation_event(self, event):
        # print time, state, event queue
        if self.output:
            print()
            print("Time: {}; state: {}".format(self.time, self.state))
            eq = self.simulator.event_queue.render(sim_obj=self, as_list=True)
            if eq is None:
                print("Empty event queue")
            else:
                times = [ev[1] for ev in eq[1:]]
                print("Event queue times: {}".format(times))
        self.state += random.choice([-1, 1])
        for i in range(random.choice([0, 1, 2])):
            self.send_event(random.choice([1, 6]), self, MessageSentToSelf())

    event_handlers = [(MessageSentToSelf, handle_simulation_event)]

    # register the message types sent
    messages_sent = [MessageSentToSelf]


class RunRandomStateVariableSimulation(object):

    @staticmethod
    def parse_args(cli_args=None):  # pragma: no cover  # don't bother testing
        """ Parse command line arguments

        Args:
            cli_args (:obj:`list`, optional): if provided, use to test command line parsing

        Returns:
            :obj:`argparse.Namespace`: parsed command line arguements
        """
        parser = argparse.ArgumentParser(
            description="A trivial simulation that increments or decrements a variable at each event")
        parser.add_argument('initial_state', type=int, help="Initial state")
        parser.add_argument('time_max', type=float, help="End time for the simulation")
        parser.add_argument('--no-output', dest='output', action='store_false',
                            help="Don't write progress to stdout")
        if cli_args is not None:
            args = parser.parse_args(cli_args)
        else:    # pragma: no cover     # reachable only from command line
            args = parser.parse_args()
        return args

    @staticmethod
    def main(args):

        # create a simulator
        simulator = SimulationEngine()

        # create a simulation object and add it to the simulation
        simulator.add_object(RandomStateVariableSimulationObject('random state variable object',
                                                                 args.initial_state, args.output))

        # run the simulation
        simulator.initialize()
        num_events = simulator.simulate(args.time_max)
        sys.stderr.write("Executed {} event(s).\n".format(num_events))
        return(num_events)


if __name__ == '__main__':  # pragma: no cover     # reachable only from command line
    try:
        args = RunRandomStateVariableSimulation.parse_args()
        RunRandomStateVariableSimulation.main(args)
    except KeyboardInterrupt:
        pass
