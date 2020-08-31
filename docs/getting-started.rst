Getting started
===============

The following examples and tutorials illustrate how to use *DE-Sim* to build and simulate models.

-----------------------------------
Examples
-----------------------------------

* `Minimal simulation <https://github.com/KarrLab/de_sim/blob/master/de_sim/examples/minimal_simulation.py>`_: a minimal example of a simulation
* `Random walk <https://github.com/KarrLab/de_sim/blob/master/de_sim/examples/random_walk.py>`_: a one-dimensional random walk model, with random times between steps
* `Parallel hold (PHOLD) <https://github.com/KarrLab/de_sim/blob/master/de_sim/examples/phold.py>`_: a model developed by Richard Fujimoto to benchmark parallel discrete-event simulators
* `Epidemic <https://github.com/KarrLab/de_sim/blob/master/de_sim/examples/sirs.py>`_: two SIR models of an infectious disease epidemic

These examples have corresponding unit tests which run them in the *DE-Sim*'s `directory of unit tests of examples <https://github.com/KarrLab/de_sim/tree/master/tests/examples>`_.

-----------------------------------
Interactive tutorials
-----------------------------------

Please see `sandbox.karrlab.org <https://sandbox.karrlab.org/tree/de_sim>`_ for interactive Jupyter notebook tutorials about designing, building and simulating models with *DE-Sim*.
It includes tutorials that use the random walk, PHOLD, and epidemic models listed above.

-----------------------------------
Template for models and simulations
-----------------------------------

The minimal simulation, located at `de_sim/examples/minimal_simulation.py <https://github.com/KarrLab/de_sim/blob/master/de_sim/examples/minimal_simulation.py>`_, can be used as a template for implementing and simulating a model with *DE-Sim*.
