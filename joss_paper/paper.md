---
title: 'DE-Sim: an object-oriented, discrete-event simulation tool for complex, data-driven modeling in Python'
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
 - name: Icahn Institute for Data Science and Genomic Technology, and Department of Genetics and Genomic Sciences, Icahn School of Medicine at Mount Sinai, New York, NY 10029, USA
   index: 1
date: 3 August 2020
bibliography: paper.bib
---

# Summary

Many fields of science and engineering use mechanistic models to understand how the dynamics of complex systems arise from the interactions among their components. Often, these models approximate these interactions as instantaneous, or discrete, events. Such models are called *discrete-event models*. For example, discrete-event models are frequently used to study the dynamics of biochemical networks, characterize the performance of computer networks, evaluate potential war strategies, and forecast epidemics [@banks2005discrete]. These discrete event models can be simulated using the *discrete-event simulation* (DES) method [@fishman2013discrete].

To make it easier to construct and simulate complex discrete-event models, we developed DE-Sim ([github.com/KarrLab/de_sim](https://github.com/KarrLab/de_sim)), an open-source, Python-based DES tool. DE-Sim supports two main functions. First, DE-Sim users can define discrete-event models as object-oriented Python programs. Second, DE-Sim conveniently and efficiently simulates these models.

# The need for tools that help researchers build and simulate complex models

DE-Sim simplifies the construction and simulation of discrete-event models. 

The complexity of large discrete-event models makes them challenging to construct. They can contain multiple types of components, and multiple types of interactions between components. DE-Sim addresses this challenge by structuring discrete-event models as object-oriented programs. This approach, known as *object-oriented discrete-event simulation* (OO DES), implements the components of models as simulation objects and implements their interaction events as messages that schedule the simulations objects to execute events at specific times [@zeigler1987hierarchical]. With DE-Sim, users define classes of simulation object by subclassing DE-Sim’s base simulation object class and specifying their behavior. Complex systems that contain multiple types of components can be easily modeled in DE-Sim by creating multiple classes of simulation objects. Users can model arbitrarily many instances of a type of component creating multiple instances of the corresponding simulation object class. DE-Sim simulation objects can exploit all the features of Python objects. For example, hierarchical refinement relationships among the components in a system being modeled can be mirrored by subclass relationships among the simulation object types that represent the components in a DE-Sim model. We believe that DE-Sim’s use of OO programming to construct discrete-event models simplifies and accelerates the design and development of models.

Recent advances in data collection have enabled many scientific fields to collect detailed data about the components of complex systems and their interactions. For example, the revolution in deep sequencing has dramatically increased the availability of molecular data. These data be used to parameterize discrete-event models. Dynamical models constructed with DE-Sim can leverage Python's extensive suite of high-quality data science tools to easily manage and integrate large, heterogeneous, multidimensional data into models. For example, tools such as NumPy [@oliphant2006guide], pandas [@mckinney2010data], SciPy [@virtanen2020scipy], and SQLAlchemy [@bayer2020sqlalchemy] can be used by DE-Sim models to store and integrate model inputs, simplify analyses during simulation, and organize and save predictions for downstream analysis.

DE-Sim is designed for scientists and engineers who want to build and use quantitative, dynamical models to understand the properties of complex, discrete-time systems. DE-Sim's features address the needs of this audience: it uses Python, one of the most popular languages; it is open-source; it is easy to learn because it provides several tutorials, examples, and documentation; and it is thoroughly tested. We are already using DE-Sim to develop a multi-algorithmic simulator that simulates comprehensive models of biological cells which predict phenotype from genotype by capturing all of the biochemical activity in a cell.

# Comparison of DE-Sim with existing discrete-event simulation tools

Multiple DES tools already exist.
\autoref{fig:comparison} lists the most frequently cited DES tools.
These tools all provide a programming environment for developing DES models, a simulator that simulates models, and methods for recoding simulation predictions.

![**Comparison of DE-Sim with important existing DES tools.**
DE-Sim is the only open-source, object-oriented, discrete-event simulation tool based on Python.
This combination of features makes DE-Sim uniquely suitable for creating discrete-event models for studying complex systems. It combines the power and convenience of OO modeling with the ability to leverage Python's extensive library of data science tools to manage and analyze the large datasets needed by models of complex systems.
\label{fig:comparison}](comparison.pdf)

In addition, two tools provide a graphical interface for describing models, SIMUL8 [@concannon2003dynamic] and SimEvents [@clune2006discrete].
The commercial simulation tools all use proprietary modeling languages.
DE-Sim and three other tools, SystemC [@mueller2001simulation], SIMSCRIPT III [@rice2005simscript] and SimEvents support object-oriented descriptions of models [@zeigler1987hierarchical].
SimEvents obtains its OO modeling functionality from the OO features of Simulink.

In contrast with SimPy [@matloff2008introduction], DE-Sim models are defined using object-oriented programs, whereas SimPy models must be defined with functions at a lower-level.
In addition, DE-Sim supports a uniform approach for scheduling events, whereas SimPy models that contain multiple interacting processes must use two approaches to schedule events.
DE-Sim objects always schedule an event by sending an event message to the object that will execute the event.
However, SimPy processes schedule events for themselves by using a timeout call and Python's `yield` function, but schedule events for other processes by raising an interrupt exception.

DE-Sim is more accessible to scientific researchers than SystemC, because DE-Sim builds upon Python whereas SystemC uses C++, a lower-level language.
In addition, because SystemC is designed for modeling digital electronics, its concepts do not map well onto the systems that scientific researchers study.
The last three DES tools in \autoref{fig:comparison} are commercial software.
Two of them, SIMUL8 and SimEvents, specialize in modeling domains that do not contain scientific problems.

Modelers often use space-time diagrams of OO DES simulation runs (\autoref{fig:phold_space_time_plot}) helpful for designing, understanding and debugging discrete-event models.
DE-Sim automatically generate these diagrams from log files.

![**DE-Sim can generate space-time visualizations of simulation trajectories.** 
This figure illustrates a space-time visualization of all of the events and messages in a simulation of the parallel hold (PHOLD) parallel DES benchmark model [@fujimoto1990performance] with three simulation objects. The timeline (grey line) for each object shows its events (grey dots). Each event in PHOLD schedules another event, as illustrated by event messages (arrows) sent from the earlier event to the event being scheduled. The curved blue arrows indicate events scheduled by a simulation object for itself in the future, while the straight purple arrows indicate event messages sent to other simulation objects. The programs for the PHOLD model and for visualizing the trajectory of any simulation are available in the DE-Sim Git repository. 
\label{fig:phold_space_time_plot}](phold_space_time_plot.pdf)

An important benefit of OO DES models is that individual simulation runs may be sped up by parallel execution on multiple cores.
More precisely, the simulation of an OO DES model composed of objects that only interact with each other vian event messages and do not access shared memory might be sped up by distributing its objects across multiple cores and executing them in parallel.
This simulation would need to be synchronized by a parallel DES simulator, such as Time Warp [@Jefferson1985, @carothers2000ross].
Parallel DES simulations can achieve substantial speedup, as Barnes et al. demonstrated by running the PHOLD benchmark on nearly 2 million cores [@Barnes2013].
By contrast, while independent SimPy simulations can be run in parallel, a single SimPy simulation cannot be parallelized [@muller2011running].

# Tutorial: Building and simulating models with DE-Sim


A simple DE-Sim model can be defined in three steps: define an event message class; define a simulation object class; and build and run a simulation.
We illustrate this process with a model of a random walk on the integer number line. 

1: Create an event message class by subclassing `EventMessage`.

Each DE-Sim event contains an event message that provides data needed by the simulation object that executes the event.
The random walk model sends event messages that contain the size of the random step.

```python
import de_sim

class RandomStepMessage(de_sim.EventMessage):
    " An event message class that specifies a random walk step size "
    attributes = ['step']
```
The attribute `attributes` In the definition of `RandomStepMessage` is a special attribute of an `EventMessage` that provides a list of the names of a message class' attributes.
It is optional. 
However, an event message class must be documented by a docstring.

2: Define a simulation object class by subclassing `SimulationObject`.

Instantiated simulation objects are like threads, in that a simulation's scheduler decides when to execute them, and their execution is suspended when they have no work to do.
But DES simulation objects and threads are scheduled by different algorithms.
Whereas threads are scheduled whenever they have work to do,
a DES scheduler schedules simulation objects to ensure that events occur in simulation time order, as summarized by the fundamental rule of discrete-event simulation:

1. All events in a simulation are executed in non-decreasing time order.

By guaranteeing this behavior, the DE-Sim scheduler ensures that causality relationships between events are respected.
(We write *non-decreasing* instead of *increasing* time order because events can occur simultaneously.
Simultaneous events are addressed in the [features section](#summary-of-desims-key-features).)

This rule has two consequences:

1. All synchronization between simulation objects is controlled by the simulation times of events.
2. Each simulation object executes its events in increasing time order.

Subclasses of `SimulationObject`, called *simulation object classes*, are Python classes that generate and handle simulation events.
They are created by a custom class creation method for `SimulationObject` that gives special meaning to certain methods and attributes.

Below, we define a simulation class that models a random walk, and illustrates all key features of `SimulationObject`.
To add variety to its temporal behavior we modify the traditional random walk by randomly selecting the time delay between steps.

```python
import random

class RandomWalkSimulationObject(de_sim.SimulationObject):
    " A 1D random walk model, with random delays between steps "

    def __init__(self, name):
        super().__init__(name)

    def schedule_next_step(self):
        " Schedule the next event "
        # A step moves -1 or +1 with equal probability
        step = random.choice([-1, +1])
        # The time between steps is 1 or 2, with equal probability
        self.send_event(random.choice([1, 2]), self, RandomStepMessage(step))

    def init_before_run(self):
        " Initialize before a simulation run; called by the simulator "
        self.position = 0
        self.history = {'times': [0],
                        'positions': [0]}
        self.schedule_next_step()

    def handle_step_event(self, event):
        " Handle a step event "
        # Update the position and history
        step = event.message.step
        self.position += step
        self.history['times'].append(self.time)
        self.history['positions'].append(self.position)
        self.schedule_next_step()

    # event_handlers contains pairs that maps each event message class
    # received by this simulation object to the method that handles
    # the event message class
    event_handlers = [(RandomStepMessage, handle_step_event)]

    # messages_sent registers all message types sent by this object
    messages_sent = [RandomStepMessage]
```

Subclasses of `SimulationObject` use these special methods and attributes.

* Special `SimulationObject` methods:
    1. `init_before_run` (optional): immediately before a simulation run, after all simulation objects have been added to a `Simulator`, the simulator calls `init_before_run` in each simulation object. Simulation object classes can send initial events and perform other initialization in `init_before_run`. For example, in `RandomWalkSimulationObject`, `init_before_run` schedules the object's first event and initializes the simulation object's position and history attributes. To initiate a simulation's execution, at least one simulation object in the simulation must schedule one initial event.
    2. `send_event`: `send_event(delay, receiving_object, event_message)` schedules an event to occur `delay` time units in the future at simulation object `receiving_object`, which will execute a simulation event containing `event_message`. An event can be scheduled for any simulation object in a simulation, including the object scheduling the event, as shown in `RandomWalkSimulationObject`. `event_message` must be an instance of an `EventMessage`. 
The event will be executed at its scheduled simulation time by an event handler in the simulation object `receiving_object`.
The handler has a parameter that receives a simulation event which contains `event_message`. In this example all simulation events are scheduled to be executed by the object that creates the event, but most realistic simulations contain multiple simulation objects which schedule events for each other. 
Object-oriented DES terminology also describes the event message as being sent by the sending object at the message's send time (the simulation time when the sending object schedules the event) and being received by the receiving object at the event's receive time (the simulation time when the event is executed). An event message can thus be viewed as a directed edge in simulation space-time from (sending object, send time) to (receiving object, receive time), as illustrated by \autoref{fig:phold_space_time_plot}.
    3. event handlers: an event handler is a method that handles a simulation event. Event handlers have the signature `event_handler(self, event)`, where `self` is the simulation object that handles (receives) the event, and `event` is a DE-Sim simulation event (`de_sim.Event`). A subclass of `SimulationObject` must define at least one event handler, like `handle_step_event` in `RandomWalkSimulationObject` above.

* Special `SimulationObject` attributes:
    1. `event_handlers`: the attribute `event_handlers` must contain an iterator over pairs that maps each event message class received by a subclass of `SimulationObject` to the subclass' event handler which handles the event message class. In the example above, `event_handlers` associates `RandomStepMessage` event messages with the `handle_step_event` event handler. The DE-Sim simulator contains a scheduler that runs an object dispatch algorithm which executes an event by using the `event_handlers` attribute of the receiving object identified in the event to determine the object's method that will execute the event. It then dispatches execution to that method in the receiving object while passing the event as an argument.
    2. `messages_sent`: the types of messages sent by a subclass of `SimulationObject` must be listed in `messages_sent`. This is used to ensure that a simulation object doesn't send messages of the wrong class.
    3. `time`: `time` is a read-only simulation object attribute that always equals the current simulation time. A `RandomWalkSimulationObject` saves the value of `time` when recording its history.

3: Execute a simulation by creating a `Simulator`, instantiating simulation objects and adding them to the `Simulator`, initializing them and sending their initial event messages, and running the simulation.

The `Simulator` class simulates models.
Its `add_object` method adds a simulation object to the simulator.
Each object in a simulation must have a unique `name`.
The `initialize` method, which calls `init_before_run` methods in simulation objects, must be called before a simulation starts.
Finally, `run` simulates a model. It takes the maximum time to which the simulation can execute. `run` also takes many optional arguments, as described in the DE-Sim API documentation.

```python
# create a simulator
simulator = de_sim.Simulator()

# create a simulation object and add it to the simulation
random_walk_sim_obj = RandomWalkSimulationObject('rand_walk')
simulator.add_object(random_walk_sim_obj)

# initialize the simulation, and send initial event messages
simulator.initialize()

# run the simulation until time 10
max_time = 10
simulator.run(max_time)

# plot the random walk as a step function
import matplotlib.pyplot as plt
plt.step(random_walk_sim_obj.history['times'],
         random_walk_sim_obj.history['positions'])
plt.xlabel('time')
plt.ylabel('position')
plt.show()
```
This runs a simulation for `max_time` time units, and plots the random walk’s trajectory (\autoref{fig:random_walk_trajectory}).

![**Trajectory of a simulation of a model of a random walk on the integer number line.**
The random walk model starts at position 0 and moves +1 or -1 with equal probability at each step.
Steps take place every 1 or 2 time units, with equal probability.
This trajectory illustrates two key characteristics of discrete-event models. First, the state, in this case the position, changes at discrete times.
Second, as a consequence of the first characteristic, the state does not change in between instantaneous events, and the trajectory of any state variable is a step function.
The source code for this model is available in the DE-Sim Git repository.
\label{fig:random_walk_trajectory}](random_walk_trajectory.png)

This tutorial and additional examples are available in a [Jupyter notebook](https://sandbox.karrlab.org/notebooks/de_sim/1.%20DE-Sim%20tutorial.ipynb).

# Performance of DE-Sim

\autoref{fig:performance} shows the performance of DE-Sim simulating a model of a cyclic messaging network over range of network sizes.

![**Performance of DE-Sim simulating a model of a cyclic messaging network over a range of network sizes.** Each statistic represents the average of three simulation runs in a Docker container on a 2.9 GHz Intel Core i5 processor. 
The cyclic messaging network model consists of a ring of simulation objects. Each object executes an event at every time unit and schedules an event for the next object in the ring 1 time unit in the future. 
Each simulation run executes for 100 time units.
The number of simulation objects in the ring is given by **Nodes**. 
The source code for this model is available in the DE-Sim Git repository.
\label{fig:performance}](performance.pdf)

# Case study: a multi-algorithmic simulation tool for whole-cell modeling implemented using DE-Sim

We have used DE-Sim to develop WC-Sim [@goldberg2020wc_sim], a multi-algorithmic simulation tool that simulates comprehensive whole-cell models of the biochemical dynamics inside biological cells [@karr2015principles; @goldberg2018emerging; @karr2012whole]. 
Whole-cell models which predict phenotype from genotype by representing all of the biochemical activity in a cell have great potential to help scientists elucidate the basis of cellular behavior, help bioengineers rationally design biosensors and biomachines, and help physicians personalize medicine.

Due to the diverse timescales of the reactions inside cells, one promising way to simulate whole-cell models is to simulate each reaction with an appropriate algorithm for its scale. For example, slow biochemical reactions, such as transcription, can be simulated with the Stochastic Simulation Algorithm (SSA, @gillespie1977exact). Faster processes, such as signal transduction, can be simulated with ordinary differential equations (ODEs). Metabolism, another fast process, can be simulated with flux-balance analysis (FBA, @orth2010flux). Simulating entire cells requires co-simulating SSA, ODE and FBA. However, tools for co-simulating these algorithms do not exist.

To accelerate whole-cell modeling, we have created WC-Sim, a tool for simulating multi-algorithmic whole-cell models described in the WC-Lang language [@karr2020wc_lang].
We implemented WC-Sim by using DE-Sim to construct a simulation object class for each of SSA, ODE, and FBA.
DE-Sim event messages schedule the activities of each simulation object, while the exact simulation time of events is used to coordinate the objects’ shared access to the counts of molecules that represent the shared state of the cell.
DE-Sim’s object-oriented modeling functionality made it easy to separately develop SSA, ODE, and FBA simulation objects and compose them into a multi-algorithmic simulator.
DE-Sim’s discrete-event framework provided the control needed to  synchronize the interactions between these classes of objects.
In addition, DE-Sim’s Python foundation enabled us to dramatically reduce the effort required to build WC-Sim by leveraging data-science tools including pandas, networkx, matplotlib, NumPy, and SciPy.
We anticipate that WC-Sim will enable researchers to conduct unprecedented simulation experiments about cellular biochemistry.

# Summary of DE-Sim’s key features

DE-Sim provides the following features that help users build and simulate complex, data-driven, discrete-event models:

* **Object-oriented modeling:** DE-Sim enables modelers to use object-oriented Python programming to build models. This makes it easy to construct complex models.
* **Access to Python’s data-science tools:** By building on Python, DE-Sim enables researchers to use high-level data science packages such as NumPy, pandas, and SciPy to integrate large, heterogeneous datasets to build models and analyze their simulations.
* **Simple simulation logging:** DE-Sim supports easily configured, high performance Python logs which can log simulation data that help users debug their models.
* **Checkpointing of simulation state:** DE-Sim can checkpoint the state of a simulation to a file.
A record of the predictions made by a simulation run are easily obtained by subclassing a DE-Sim abstract class that creates periodic checkpoints.
In addition, DE-Sim automatically records configuration information such as a simulation run’s arguments and metadata such as the start time and duration of the simulation.
* **Powerful stop conditions:** DE-Sim makes it easy to implement complex stop conditions. These are implemented as arbitrary Python functions that return true when the simulation should be terminated.
* **Space-time visualizations for analysis and debugging:** DE-Sim can generate space-time visualizations of simulation trajectories (\autoref{fig:phold_space_time_plot}). These diagrams help understand and debug models.
* **Reproducible simulations:** DE-Sim simulation runs are *reproducible*, which means that repeated executions of a simulation with the same input -- including seeds for random number generators -- will produce exactly the same simulation trajectories.
* **Controlled, reproducible execution of simultaneous events:** An OO discrete-event simulation may contain simultaneous events. A simulation object may receive multiple events simultaneously, and multiple simulation objects may receive events at the same simulation time. 
In both of these cases DE-Sim provides discrete-event models with full and convenient control over the execution order of simultaneous messages.

# Conclusion

# Availability of DE-Sim

DE-Sim is freely and openly available under the MIT license at the locations below.

* Python package: [PyPI: de-sim](https://pypi.org/project/de-sim/)
* Docker image: [DockerHub: karrlab/de_sim](https://hub.docker.com/r/karrlab/de_sim)
* Tutorials: Jupyter notebooks at [https://sandbox.karrlab.org](https://sandbox.karrlab.org/tree/de_sim)
* Installation instructions and documentation of DE-Sim’s API: [docs.karrlab.org](https://docs.karrlab.org/de_sim/)
* Issue tracker: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/issues/)
* Source code: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/)
* Guide to contributing to DE-Sim and code of conduct for developers: [GitHub: KarrLab/de_sim](https://github.com/KarrLab/de_sim/)
* Continuous integration: [CircleCI: gh/KarrLab/de_sim](http://circleci.com/gh/KarrLab/de_sim/)

DE-Sim requires [Python](https://www.python.org/) 3.7 or higher and [pip](https://pip.pypa.io/).

This article discusses version 0.0.8 of DE-Sim.

# Acknowledgements

We thank Yin Hoon Chew for her helpful feedback on this paper. This worked was supported by the National Science Foundation [award 1649014 to J.R.K.], the National
Institutes of Health [award R35GM119771 to J.R.K], and the Icahn Institute for Data Science and Genomic Technology.

# References
