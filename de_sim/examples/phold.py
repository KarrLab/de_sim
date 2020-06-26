""" A simple example simulation. Implements PHOLD.

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2016-06-10
:Copyright: 2016-2020, Karr Lab
:License: MIT
"""

import random
import sys
import argparse

from de_sim.simulation_message import SimulationMessage
from de_sim.simulation_object import ApplicationSimulationObject
from de_sim.simulation_engine import SimulationEngine
from de_sim.examples.debug_logs import logs as debug_logs


def obj_name(obj_num):
    # create object name from index
    return 'phold_{}'.format(obj_num)


def obj_index(obj_name):
    # get object index from name
    return int(obj_name.split('_')[1])


def exp_delay():
    return random.expovariate(1.0)


class MessageSentToSelf(SimulationMessage):
    "A message that's sent to self"


class MessageSentToOtherObject(SimulationMessage):
    "A message that's sent to another PHold simulation object"


class InitMsg(SimulationMessage):
    'initialization message'


MESSAGE_TYPES = [MessageSentToSelf, MessageSentToOtherObject, InitMsg]


class PholdSimulationObject(ApplicationSimulationObject):

    def __init__(self, name, args):
        self.args = args
        super().__init__(name)

    def send_initial_events(self):
        self.send_event(exp_delay(), self, InitMsg())

    def handle_simulation_event(self, event):
        """Handle a single simulation event."""
        # schedule event
        if random.random() < self.args.frac_self_events or self.args.num_phold_procs == 1:
            receiver = self
            self.log_debug_msg("{:8.3f}: {} sending to self".format(self.time, self.name))

        else:
            # send to another process; pick process index in [0,num_phold-2], and increment if self
            index = random.randrange(self.args.num_phold_procs - 1)
            if index == obj_index(self.name):
                index += 1
            receiver = self.simulator.simulation_objects[obj_name(index)]
            self.log_debug_msg("{:8.3f}: {} sending to {}".format(self.time, self.name,
                                                                  obj_name(index)))

        if receiver == self:
            message = MessageSentToSelf
        else:
            message = MessageSentToOtherObject
        self.send_event(exp_delay(), receiver, message())

    def get_state(self):
        return str(self.args)

    def log_debug_msg(self, msg):
        log = debug_logs.get_log('de_sim.debug.example.console')
        log.debug(msg, sim_time=self.time)

    event_handlers = [(sim_msg_type, 'handle_simulation_event') for sim_msg_type in MESSAGE_TYPES]

    # register the message types sent
    messages_sent = MESSAGE_TYPES


class RunPhold(object):

    @staticmethod
    def parse_args(cli_args):
        """ Parse command line arguments

        Args:
            cli_args (:obj:`list`): command line arguments

        Returns:
            :obj:`argparse.Namespace`: parsed command line arguements
        """
        parser = argparse.ArgumentParser(description="Run PHOLD simulation. "
                                         "Each PHOLD event either schedules an event for 'self' or for some other randomly selected LP, "
                                         "in either case with an exponentially-distributed time-stamp increment having mean of 1.0. "
                                         "See R. M. Fujimoto, Performance of Time Warp Under Synthetic Workloads, "
                                         "1990 Distributed Simulation Conference, pp. 23-28, January 1990 and "
                                         "Barnes PD, Carothers CD, Jefferson DR, Lapre JM. Warp Speed: Executing Time Warp "
                                         "on 1,966,080 Cores. "
                                         "SIGSIM-PADS '13. Montreal: Association for Computing Machinery; 2013. p. 327-36. ")
        parser.add_argument('num_phold_procs', type=int, help="Number of PHOLD processes to run")
        parser.add_argument('frac_self_events', type=float, help="Fraction of events sent to self")
        parser.add_argument('time_max', type=float, help="End time for the simulation")
        parser.add_argument('--seed', '-s', type=int, help='Random number seed')
        args = parser.parse_args(cli_args)

        if args.num_phold_procs < 1:
            parser.error("Must create at least 1 PHOLD process.")
        if args.frac_self_events < 0:
            parser.error("Fraction of events sent to self ({}) should be >= 0.".format(args.frac_self_events))
        if 1 < args.frac_self_events:
            parser.error("Fraction of events sent to self ({}) should be <= 1.".format(args.frac_self_events))
        if args.seed:
            random.seed(args.seed)
        return args

    @staticmethod
    def main(args):

        # create a simulator
        simulator = SimulationEngine()

        # create simulation objects, and send each one an initial event message to self
        for obj_id in range(args.num_phold_procs):
            phold_obj = PholdSimulationObject(obj_name(obj_id), args)
            simulator.add_object(phold_obj)

        # run the simulation
        simulator.initialize()
        event_num = simulator.simulate(args.time_max).num_events
        sys.stderr.write("Executed {} events.\n".format(event_num))
        return(event_num)


if __name__ == '__main__':  # pragma: no cover     # reachable only from command line
    try:
        args = RunPhold.parse_args(sys.argv[1:])
        RunPhold.main(args)
    except KeyboardInterrupt:
        pass
