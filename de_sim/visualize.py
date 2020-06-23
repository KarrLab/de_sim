""" Visualize a simulation run

:Author: Arthur Goldberg <Arthur.Goldberg@mssm.edu>
:Date: 2020-06-23
:Copyright: 2020, Karr Lab
:License: MIT
"""

'''
todo:
write get_data
docstrings
better test of plot
better use of plot_params
more constants out of plot_data()
'''

from collections import namedtuple
import matplotlib.pyplot as plt
import matplotlib.patches as patches


EventCoordinates = namedtuple('EventCoordinates', 'sim_obj_id time',)


EventMessage = namedtuple('EventMessage', 'message_type send_coordinates receive_coordinates')


class SpaceTime(object):
    """ Generate a space-time plot of a simulation run from a plot log
    """

    def __init__(self, data, plot_params=None):
        self.data = data
        # plotting parameters
        self.plot_params = plot_params
        if plot_params is None:
            self.plot_params = dict(width=1.0,
                                    time_axis_width=0.5,
                                    obj_name_font_size=8,
                                    event_line_width=6,
                                    event_dot_size=4,
                                    event_dot_color='tab:gray',
                                    msg_width=3,
                                    msg_arrow_width=6,
                                    msg_to_self_color='blue',
                                    msg_to_other_color='purple',
                                    msg_to_self_curve=30)


    def get_object_ids(self):
        object_ids = set()
        for event in self.data:
            for event_coordinate in [event.send_coordinates, event.receive_coordinates]:
                object_ids.add(event_coordinate.sim_obj_id)
        return sorted(object_ids)

    def get_min_max_times(self):
        times = []
        for event in self.data:
            for event_coordinate in [event.send_coordinates, event.receive_coordinates]:
                times.append(event_coordinate.time)
        return min(times), max(times)

    def get_obj_x_locations(self):
        num_objs = len(self.get_object_ids())
        offset = 1./(2*num_objs)
        return [offset + i/num_objs for i in range(num_objs)]

    def get_obj_x_locations_map(self):
        return dict(zip(self.get_object_ids(),
                        self.get_obj_x_locations()))

    def get_event_locations(self):
        obj_x_locations_map = self.get_obj_x_locations_map()
        events = []
        for event in self.data:
            for event_coordinate in [event.send_coordinates, event.receive_coordinates]:
                x_loc = obj_x_locations_map[event_coordinate.sim_obj_id]
                y_loc = event_coordinate.time
                events.append((x_loc, y_loc))
        return events

    def get_categorized_messages(self):
        self_messages = []
        other_messages = []
        for event_msg in self.data:
            if event_msg.send_coordinates.sim_obj_id == event_msg.receive_coordinates.sim_obj_id:
                self_messages.append(event_msg)
            else:
                other_messages.append(event_msg)
        return self_messages, other_messages

    def plot_data(self, filename):
        ### generate space-time diagram
        # plot time axes
        fig, ax = plt.subplots()
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.get_xaxis().set_ticks([])
        plt.xlim(0, 1)
        min_time, max_time = self.get_min_max_times()
        plt.ylim(min_time, max_time)
        ax.set_ylabel('Simulation time')
        plt.gca().invert_yaxis()

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
        style="Simple,tail_width=0.3,head_width=4,head_length=8"
        kw = dict(arrowstyle=style, color="k")
        obj_x_locations_map = self.get_obj_x_locations_map()
        def plot_message(message, self_message=False):
            x_loc = obj_x_locations_map[message.send_coordinates.sim_obj_id]
            y_loc = message.send_coordinates.time
            x_end = obj_x_locations_map[message.receive_coordinates.sim_obj_id]
            y_end = message.receive_coordinates.time
            connectionstyle = None
            if self_message:
                connectionstyle = "arc3,rad=.3"
            arrow = patches.FancyArrowPatch((x_loc, y_loc),
                                            (x_end, y_end),
                                            connectionstyle=connectionstyle,
                                            **kw)
            plt.gca().add_patch(arrow)

        self_messages, other_messages = self.get_categorized_messages()
        # plot messages sent by sim objects to self
        for self_message in self_messages:
            plot_message(self_message, True)

        # plot messages sent to another object
        for other_message in other_messages:
            plot_message(other_message)

        # plot object ids
        small_height = (max_time - min_time)/50
        for x_loc, object_id in zip(self.get_obj_x_locations(), self.get_object_ids()):
            y_loc = -small_height
            text = ax.text(x_loc, y_loc, object_id,
                           horizontalalignment='center',
                           verticalalignment='bottom')

        # top label
        # above the object ids
        transf = ax.transData.inverted()
        bounding_box = text.get_window_extent(renderer = plt.figure().canvas.get_renderer())
        bb_datacoords = bounding_box.transformed(transf)
        label = 'Simulation objects'
        ax.text(0.5, bb_datacoords.y1 - small_height, label,
                horizontalalignment='center',
                verticalalignment='bottom',
                fontsize=10, fontweight='bold')

        # plot legend
        # write file
        fig.savefig(filename)
        plt.show()

    def get_data(self):
        # get plot filename from config
        # extract data from plot file
        pass
