""" A minimal simulation, containing one simulation object.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2018-02-27
:Copyright: 2018-2020, Karr Lab
:License: MIT
"""
import argparse
from de_sim.simulation_engine import SimulationEngine
from de_sim.simulation_message import SimulationMessage
from de_sim.simulation_object import ApplicationSimulationObject


class MessageSentToSelf(SimulationMessage):
    "A message that's sent to self"


class MinimalSimulationObject(ApplicationSimulationObject):

    def __init__(self, name, delay):
        self.delay = delay
        super().__init__(name)

    def send_initial_events(self):
        self.send_event(self.delay, self, MessageSentToSelf())

    def handle_simulation_event(self, event):
        self.send_event(self.delay, self, MessageSentToSelf())

    def get_state(self):
        return str(self.delay)

    event_handlers = [(MessageSentToSelf, handle_simulation_event)]

    # register the message types sent
    messages_sent = [MessageSentToSelf]


class RunMinimalSimulation(object):

    @staticmethod
    def parse_args(cli_args=None):
        """ Parse command line arguments

        Args:
            cli_args (:obj:`list`, optional): if provided, use to test command line parsing

        Returns:
            :obj:`argparse.Namespace`: parsed command line arguements
        """
        parser = argparse.ArgumentParser(description="A minimal simulation, containing one simulation object")
        parser.add_argument('delay', type=float, help="Delay between events")
        parser.add_argument('time_max', type=float, help="End time for the simulation")
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
        simulator.add_object(MinimalSimulationObject('minimal_sim_obj', args.delay))

        # run the simulation
        simulator.initialize()
        num_events = simulator.simulate(args.time_max)
        return(num_events)


if __name__ == '__main__':  # pragma: no cover     # reachable only from command line
    try:
        args = RunMinimalSimulation.parse_args()
        RunMinimalSimulation.main(args)
    except KeyboardInterrupt:
        pass
