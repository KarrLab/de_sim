---
title: 'DE-Sim: An Object-Oriented Discrete-Event Simulator in Python'
tags:
  - dynamical modeling
  - simulation
  - discrete-event simulation
  - object-oriented simulation
  - parallel discrete-event simulation
  - biochemical modeling
  - whole-cell modeling
  - Python
authors:
  - name: Arthur P. Goldberg
    orcid: 0000-0003-2772-1484
    affiliation: "1"
  - name: Jonathan R. Karr
    orcid: 0000-0002-2605-5080
    affiliation: "1"
affiliations:
 - name: Icahn Institute for Data Science and Genomic Technology and Department of Genetics and Genomic Sciences, Icahn School of Medicine at Mount Sinai, New York, NY 10029, USA
   index: 1
date: 20 July 2020
bibliography: paper.bib
---

# Summary

A central challenge in science is to understand how systems behaviors emerge from complex networks. For example, systems biology seeks to understand how cellular phenotypes emerge from complex biochemical networks. Due to recent advances in data collection and storage, many scientific fields now have extensive data about a wide range of complex networks. Larger and more comprehensive models, such as models of entire cells [@karr2015principles, @goldberg2018emerging, @karr2012whole], are needed to decipher this data. However, it remains difficult to build and simulate complex models.

One of the most promising methods for simulating large models is discrete-event simulation (DES). DES represents a system as a collection of processes that can read the values of a set of shared variables and create events to modify their values at discrete instants in time. DES is ideal for large models because its discrete structure is conducive to parallel execution. For example, Barnes et al. have executed DES models using nearly 2 million cores [@Barnes2013]. Several DES frameworks are available. This includes basic frameworks such as SimPy [@matloff2008introduction] which enable scientists to implement models using functional programming; high-performance, parallelized, object-oriented frameworks such as POSE [@wilmarth2005pose] and ROSS [@carothers2002ross] which support C-based models; and commercial frameworks such as Simula8 [@concannon2003dynamic] which provide proprietary languages for describing models. DES has been applied to a wide range of models. For example, epidemiologists have used DES to simulate the transmission of infectious disease, computer engineers have used DES to simulate distributed computer networks, and the military often uses DES to simulate wars [@banks2005discrete]. However, it remains challenging to use DES for large data-driven models. It is difficult to implement complex models using functional frameworks such as SimPy, and it is difficult to use high-level data science tools such as Pandas [@mckinney2010data] with C-based frameworks such as POSE and ROSS.

To make it easier to construct and simulate complex, data-driven models, we used Python to develop DE-Sim, an open-source, object-oriented discrete-event simulation framework. Because DE-Sim is implemented in Python, DE-Sim makes it easy to use Python-based data science tools such as NumPy [@oliphant2006guide], Pandas, SciPy [@virtanen2020scipy], and SQLAlchemy [@bayer2020sqlalchemy] to build models and analyze simulation results. We have extensively tested and documented DE-Sim. As described below, DE-Sim is freely available from GitHub and PyPI.

Here, we describe the models that DE-Sim enables, outline the features of DE-Sim, provide a brief tutorial of building and simulating models with DE-Sim, analyze the performance of DE-Sim, summarize how we are using DE-Sim to develop WC-Sim [@goldberg2020wc_sim], a simulator for whole-cell models, and describe the advantages of DE-Sim over existing DES frameworks. Additional examples, tutorials, installation instructions, and source code documentation are available at [https://github.com/KarrLab/de_sim](https://github.com/KarrLab/de_sim).

# Need: simpler tools for building and simulating data-driven models

DE-Sim is needed by researchers who want to build OO DES models in Python because existing open source Python simulators do not support an object-oriented, message-passing interface.
We have used DE-Sim as a platform for a simulator of whole-cell models that comprehensively represent the biochemical dynamics in individual biological cells [@goldberg2020wc_sim; @goldberg2018emerging].
The whole-cell simulator (WC-Sim) models the growth of a cell and the changes in its biochemical composition caused by chemical reactions and the intracellular movement of molecules.
To comprehensively represent the numerous processes in a cell, such as metabolism, transcription, and translation, WC-Sim must use multiple types of dynamic integration algorithms, including ordinary differential equations and the stochastic simulation algorithm.
DE-Sim's OO DES framework enabled the construction of WC-Sim.
WC-Sim uses different DE-Sim object types to represent different integration algorithms, and uses
DE-Sim's discrete-event scheduling to synchronize the interactions between these integration algorithms.

Another benefit of implementing models in the object-oriented, message-passing framework supported by DE-Sim is that parallel DES simulation can reduce the runtimes of their simulations, which are often inconveniently long.
The OO DES framework makes parallel simulation feasible because 1) objects that do not share memory references can be distributed on multiple processors, and 2) a parallel DES simulator interfaces with simulation objects through the event messages that they use to schedule events [@Jefferson1985; @Barnes2013; @Carothers2000].
An example research model accelerated by parallel simulation analyzes epidemic outbreak phenomena [@perumalla2012discrete].
We plan to speed up whole-cell models of human cells with parallel simulation in future work [@goldberg2016toward].

# Key features

DE-Sim offers the following features:

* **Object-oriented Python models:** DE-Sim enables researchers to use object-oriented Python programming to build models. This makes it easy to use large datasets and packages such as NumPy, Pandas, SciPy, and SQLAlchemy to build complex data-driven models.
* **Stop conditions:** DE-Sim make it easy to use Python functions to implement stop conditions. These functions simply must return true when the simulation state has reached one or more stop conditions.
* **Recording simulation trajectories:** DE-Sim can record the results of each simulation, as well as metadata such as its start time, run time, and the IP address of the machine which executed the simulation.
* **Space-time visualizations:** DE-Sim can generate space-time visualization of simulation trajectories (\autoref{fig:phold_space_time_plot}). These diagrams can be valuable tools for understanding and debugging models.
* **Checkpointing:** DE-Sim can checkpoint the state of simulations. These checkpoints can be used to restart or debug simulations. Checkpointing is particularly helpful for using DE-Sim on clusters that have short execution limits or for using DE-Sim on spot-priced virtual machines in the commercial cloud.
* --
* **Simulation configuration:** DE-Sim simulations can be configured using simple text files. These files can be used to control XXX.
* **Model validation:** Extensive error detection

![A space-time visualization of all messages and events in an 8 time unit simulation of the PHOLD parallel DES benchmark with exponentially-distributed event delays with $\mu=1$ and a probability of 0.5 of objects scheduling the next event for themselves [@fujimoto1990performance; @Barnes2013].
A timeline for each object shows its events as gray dots.
Event messages are shown as arrows, with the arrow tail located at the (object instance, simulation time) coordinates when an event message was created and sent, and the arrow head located at the coordinates when the event message is executed.
At time 0 each PHOLD object sends an initialization message to itself.
Curved blue arrows represent event messages sent by objects to themselves, while straight purple arrows illustrate messages sent to another object. The source code for the PHOLD model is available in the DE-Sim Git repository.
\label{fig:phold_space_time_plot}](phold_space_time_plot.png)

# Tutorial: Building and simulating models

A OO DES application that uses DE-Sim can be defined in three steps:

1: Create event message types by subclassing `SimulationMessage`.

```python
class MessageSentToSelf(SimulationMessage):
    "A message type with no attributes"

class MessageWithAttribute(SimulationMessage):
    'An event message type with an attribute'
    attributes = ['attr_1']
```

An event message class must be documented by a docstring, and may include attributes.

2: Define simulation application objects by subclassing `ApplicationSimulationObject`.

```python
class SimpleSimulationObject(ApplicationSimulationObject):

    def __init__(self, name, delay):
        self.delay = delay
        super().__init__(name)

    def send_initial_events(self):
        self.send_event(self.delay, self, MessageSentToSelf())

    def handle_simulation_event(self, event):
        self.send_event(self.delay, self, MessageSentToSelf())

    event_handlers = [(MessageSentToSelf, handle_simulation_event)]

    # register the message types sent
    messages_sent = [MessageSentToSelf]
```

Each simulation object must have a unique `name`.
This example adds an instance attribute that provides the delay between events.
All `ApplicationSimulationObject`s also have a read-only attribute called `time` that always provides the current simulation time.

A simulation object may include a `send_initial_events` method, which, if present, will be called by the simulator during initialization to send the object's initial events.
A simulation must send at least one initial event.

A simulation object must include at least one method that handles simulation events.
The simulator vectors incoming message types as directed by an `event_handlers` attribute that associates each message type received by a simulation object with one of its methods.

`ApplicationSimulationObject` provides the method
`send_event(delay, receiving_object, event_message)` which schedules an event to occur `delay` time units in the future.
`event_message` is an instance of a `SimulationMessage`, and may have attributes that contain data used by the event.
The event will be executed by an event handler in simulation object `receiving_object`, which will receive a simulation event containing `event_message` at its scheduled simulation time.
In this example all simulation events are scheduled to be executed by the object that creates the event, but realistic
simulations contain multiple simulation objects which schedule events for each other.

3: Execute a simulation by creating a `SimulationEngine`, instantiating the application objects, sending their initial event messages, and running the simulation.

```python
# create a simulation engine
simulation_engine = SimulationEngine()

# create a simulation object and add it to the simulation
simulation_engine.add_object(SimpleSimulationObject('object_1', 6))

# initialize and run the simulation
simulation_engine.initialize()
num_events = simulation_engine.run(25)
```
This runs a simulation for 25 time units, and obtains the number of events executed.

# Performance

DE-Sim achieves good performance by using Python's `heapq` priority queue package to schedule events.
\autoref{fig:performance} reports the performance of DE-Sim over a range of simulation sizes.

![Performance of DE-Sim executing a simulation that sends events around a cycle of objects.
We present the statistics of three runs made in a Docker container executing on a 2.9 GHz Intel Core i5 processor in a MacBook.
\label{fig:performance}](performance.png)

# Case study: a simulator for whole-cell models

# Comparison with other DES frameworks

* Low-level frameworks in high-level languages
  * SimPy
* High-performance C-based frameworks
  * POSE
  * ROSS
* Commercial frameworks with proprietary modeling languages
  * Simul8

# Availability

DE-Sim is freely and openly available under the MIT license at the locations below.

* Python package: [PyPI: de-sim](https://pypi.org/project/de-sim/)
* Docker image: [DockerHub: karrlab/de_sim](https://hub.docker.com/r/karrlab/de_sim)
* Examples, tutorials, and documentation: [docs.karrlab.org](https://docs.karrlab.org/de_sim/)
* Issue tracker: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/issues/)
* Source code: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/)
* Guide to contributing and code of conduct: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/)
* Continuous integration: [CircleCI: gh/KarrLab/de_sim](http://circleci.com/gh/KarrLab/de_sim/)

DE-Sim requires [Python](https://www.python.org/) 3.6 or higher and [pip](https://pip.pypa.io/).

This article discusses version 0.0.3 of DE-Sim.

# Acknowledgements

This worked was supported by the National Science Foundation [award 1649014 to J.R.K.], the National
Institutes of Health [award R35GM119771 to J.R.K], and the Icahn Institute for Data Science and Genomic Technology.

# References
