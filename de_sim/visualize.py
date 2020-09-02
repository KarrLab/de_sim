""" Visualize a simulation run

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-23
:Copyright: 2020, Karr Lab
:License: MIT
"""

# TODO(Arthur): filtering for large traces
# TODO(Arthur): plot legend, plot metadata

from collections import namedtuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches


EventCoordinates = namedtuple('EventCoordinates', 'sim_obj_id time',)
EventCoordinates.__doc__ += ': the coordinates of an event: (simulation object id, simulation time)'
EventCoordinates.sim_obj_id.__doc__ += ': the unique name of a simulation object'
EventCoordinates.time.__doc__ += ': the event time of an event'


SimulationEventMessage = namedtuple('SimulationEventMessage', 'message_type send_coordinates receive_coordinates')
SimulationEventMessage.__doc__ += ': a simulation event message; its type, and send and receive coordinates'
SimulationEventMessage.message_type.__doc__ += ': the class name of a simulation event message'
SimulationEventMessage.send_coordinates.__doc__ += ': an :obj:`EventCoordinates`: the send coordinates'
SimulationEventMessage.receive_coordinates.__doc__ += ': an :obj:`EventCoordinates`: the receive coordinates'


class SpaceTime(object):
    """ Generate a space-time plot of a simulation run from a plot log
    """

    def __init__(self, data=None, plot_params=None):
        if data is not None:
            self.data = data
        # plotting parameters
        self.plot_params = plot_params
        if plot_params is None:
            self.plot_params = dict(time_axis_width=0.5,
                                    obj_name_font_size=8,
                                    event_line_width=6,
                                    event_dot_size=4,
                                    event_dot_color='tab:gray',
                                    msg_width=0.3,
                                    msg_arrow_width=3,
                                    msg_arrow_length=6,
                                    # not a radius, as larger values make tighter curves, but that's
                                    # what matplotlib calls it
                                    msg_self_arrow_radius=0.4,
                                    msg_to_self_color='blue',
                                    msg_to_other_color='purple')

    def get_object_ids(self):
        """ Get ids of all objects from the list of event messages
        """
        object_ids = set()
        for event in self.data:
            for event_coordinate in [event.send_coordinates, event.receive_coordinates]:
                object_ids.add(event_coordinate.sim_obj_id)
        return sorted(object_ids)

    def get_min_max_times(self):
        """ Get the minimum and maximum event times from the list of event messages
        """
        times = []
        for event in self.data:
            for event_coordinate in [event.send_coordinates, event.receive_coordinates]:
                times.append(event_coordinate.time)
        return min(times), max(times)

    def get_obj_x_locations(self):
        """ Get the x locations of the events for all objects
        """
        num_objs = len(self.get_object_ids())
        offset = 1. / (2 * num_objs)
        return [offset + i / num_objs for i in range(num_objs)]

    def get_obj_x_locations_map(self):
        """ Get a map from the ids of all objects to their x locations
        """
        return dict(zip(self.get_object_ids(),
                        self.get_obj_x_locations()))

    def get_event_locations(self):
        """ Get a list of the plot coordinates for all simulation events
        """
        obj_x_locations_map = self.get_obj_x_locations_map()
        events = []
        for event in self.data:
            for event_coordinate in [event.send_coordinates, event.receive_coordinates]:
                x_loc = obj_x_locations_map[event_coordinate.sim_obj_id]
                y_loc = event_coordinate.time
                events.append((x_loc, y_loc))
        return events

    def get_categorized_messages(self):
        """ Categorize all messages as to self or to other object
        """
        self_messages = []
        other_messages = []
        for event_msg in self.data:
            if event_msg.send_coordinates.sim_obj_id == event_msg.receive_coordinates.sim_obj_id:
                self_messages.append(event_msg)
            else:
                other_messages.append(event_msg)
        return self_messages, other_messages

    def plot_data(self, plot_filename):
        """ Generate space-time diagram

        Args:
            plot_filename (:obj:`str`): pdf filename for plot that is produced
        """
        # plot time axes
        fig, ax = plt.subplots()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.get_xaxis().set_ticks([])
        plt.xlim(0, 1)
        min_time, max_time = self.get_min_max_times()
        plt.ylim(min_time, 1.02 * max_time) # continue plot slightly beyond the last event
        ax.set_ylabel('Time', fontsize=10)
        plt.gca().invert_yaxis()
        plt.yticks(fontsize=8)

        # plot event lines
        for x_location in self.get_obj_x_locations():
            ax.plot([x_location, x_location], [min_time, max_time], color='black',
                    linewidth=self.plot_params['time_axis_width'])

        # plot event dots
        for x_loc, y_loc in self.get_event_locations():
            ax.plot(x_loc, y_loc, 'o',
                    markersize=self.plot_params['event_dot_size'],
                    color=self.plot_params['event_dot_color'],
                    clip_on=False)

        # plot messages
        arrowstyle = (f"Simple, tail_width={self.plot_params['msg_width']}, "
                      f"head_width={self.plot_params['msg_arrow_width']}, "
                      f"head_length={self.plot_params['msg_arrow_length']}")
        kw_args = dict(arrowstyle=arrowstyle)
        obj_x_locations_map = self.get_obj_x_locations_map()

        def plot_message(message, self_message=False):
            x_loc = obj_x_locations_map[message.send_coordinates.sim_obj_id]
            y_loc = message.send_coordinates.time
            x_end = obj_x_locations_map[message.receive_coordinates.sim_obj_id]
            y_end = message.receive_coordinates.time
            connectionstyle = None
            kw_args['color'] = self.plot_params['msg_to_other_color']
            if self_message:
                connectionstyle = f"arc3,rad={self.plot_params['msg_self_arrow_radius']}"
                kw_args['color'] = self.plot_params['msg_to_self_color']
            arrow = patches.FancyArrowPatch((x_loc, y_loc),
                                            (x_end, y_end),
                                            connectionstyle=connectionstyle,
                                            **kw_args)
            plt.gca().add_patch(arrow)

        self_messages, other_messages = self.get_categorized_messages()
        # plot messages sent by sim objects to self
        for self_message in self_messages:
            plot_message(self_message, True)

        # plot messages sent to another object
        for other_message in other_messages:
            plot_message(other_message)

        # plot object ids
        small_height = (max_time - min_time) / 50
        for x_loc, object_id in zip(self.get_obj_x_locations(), self.get_object_ids()):
            y_loc = -small_height
            text = ax.text(x_loc, y_loc, object_id,
                           horizontalalignment='center',
                           verticalalignment='bottom',
                           fontsize=8)

        # top label
        # above the object ids
        transf = ax.transData.inverted()
        bounding_box = text.get_window_extent(renderer=plt.figure().canvas.get_renderer())
        bb_datacoords = bounding_box.transformed(transf)
        label = 'Simulation object'
        ax.text(0.5, bb_datacoords.y1 - small_height, label,
                horizontalalignment='center',
                verticalalignment='bottom',
                fontsize=10, fontweight='normal')

        # write file
        fig.savefig(plot_filename, bbox_inches='tight', pad_inches=0)
        plt.show()

    def get_data(self, plot_file):
        """ Extract event message data from plot file

        Args:
            plot_file (:obj:`str`): filename of log with event data

        Returns:
            :obj:`list` of :obj:`SimulationEventMessage`: list of all event messages in simulation run
        """
        # 1. open file
        event_messages = []
        with open(plot_file, 'r') as file:
            # 2. ignore 1st line, with timestamp
            file.readline()
            # 3. parse each following line
            while True:
                line = file.readline()
                if not line:
                    break
                line = line.strip()
                # 3A. split line on tabs
                timestamp_n_send_time, receive_time, sender_id, receiver_id, msg_type = line.split('\t')
                receive_time = receive_time.split(',')[0]
                # 3B. split timestamp_n_send_time on ';'
                _, send_time = timestamp_n_send_time.split(';')
                send_time = send_time.strip()
                # 3C. extract times from send_time and receive_time
                send_time = float(send_time.strip('(,)'))
                receive_time = float(receive_time.strip('(,)'))
                # create SimulationEventMessage
                send_coordinates = EventCoordinates(sender_id, send_time)
                receive_coordinates = EventCoordinates(receiver_id, receive_time)
                event_message = SimulationEventMessage(msg_type, send_coordinates, receive_coordinates)
                event_messages.append(event_message)
        self.data = event_messages
        return event_messages
