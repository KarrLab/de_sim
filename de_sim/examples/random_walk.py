""" A simulation of a random walk where a variable is incremented or decremented with equal probability at each event

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-27
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""
import argparse
import random
import sys

import de_sim


class MessageSentToSelf(de_sim.SimulationMessage):
    "A message that's sent to self"


class RandomWalkSimulationObject(de_sim.ApplicationSimulationObject):
    """ The random state variable model

    * State: a number
    * Event scheduling: schedule events randomly
    * Event execution: randomly increment or decrement the state
    """

    def __init__(self, name, initial_value, output=True):
        self.state = initial_value
        self.output = output
        super().__init__(name)

    def init_before_run(self):
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


class RunRandomWalkSimulation(object):

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
        simulator = de_sim.SimulationEngine()

        # create a simulation object and add it to the simulation
        simulator.add_object(RandomWalkSimulationObject('random state variable object',
                                                                 args.initial_state, args.output))

        # run the simulation
        simulator.initialize()
        num_events = simulator.simulate(args.time_max)
        sys.stderr.write("Executed {} event(s).\n".format(num_events))
        return(num_events)


if __name__ == '__main__':  # pragma: no cover     # reachable only from command line
    try:
        args = RunRandomWalkSimulation.parse_args()
        RunRandomWalkSimulation.main(args)
    except KeyboardInterrupt:
        pass
