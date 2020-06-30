*DE-Sim* documentation
======================

*DE-Sim* is an open-source, Python-based object-oriented discrete-event simulation (DES) tool that makes it easy to use large, heterogeneous datasets and high-level data science tools such as `NumPy <https://numpy.org/>`_, `Scipy <https://scipy.org/scipylib/index.html>`_, `pandas <https://pandas.pydata.org/>`_, and `SQLAlchemy <https://www.sqlalchemy.org/>`_ to build and simulate complex computational models. Similar to `Simula <http://www.simula67.info/>`_, *DE-Sim* models are implemented by defining logical process objects which read the values of a set of shared variables and schedule events to modify their values at discrete instants in time.

To help users build and simulate complex, data-driven models, *DE-Sim* provides the following features:

* **High-level, object-oriented modeling:** *DE-Sim* makes it easy for users to use object-oriented Python programming to build models. This makes it easy to use large, heterogeneous datasets and high-level data science packages such as NumPy, pandas, SciPy, and SQLAlchemy to build complex models.
* **Powerful stop conditions:** *DE-Sim* makes it easy to implement complex stop conditions. Stop conditions can be implemented as simple Python functions that return true when the simulation state reaches the desired stop condition.
* **Simple simulation logging:** *DE-Sim* provides tools for recording the results of simulations, as well as metadata such as the start and run time of each simulation.
* **Space-time visualizations for analysis and debugging:** *DE-Sim* can generate space-time visualizations of simulation trajectories. These diagrams are valuable tools for understanding and debugging models.
* **Checkpointing for restarting and debugging:** *DE-Sim* can checkpoint the state of simulations. These checkpoints can be used to restart or debug simulations. Checkpointing is particularly helpful for using *DE-Sim* on clusters that have short time limits, or for using *DE-Sim* on spot-priced virtual machines in commercial clouds.

*DE-Sim* has been used to develop `WC-Sim <https://github.com/KarrLab/wc_sim>`_, a multi-algorithmic simulator for `whole-cell models <https://www.wholecell.org>`_.

Contents
--------

.. toctree::
   :maxdepth: 3
   :numbered:

   getting-started.rst
   installation.rst
   API documentation <source/de_sim.rst>
   performance.rst
   comparison.rst
   references.rst
   about.rst
