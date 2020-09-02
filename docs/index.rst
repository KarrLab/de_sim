*DE-Sim* documentation
======================

*DE-Sim* is an open-source, Python-based, object-oriented discrete-event simulation tool that helps modelers model complex systems.
First, *DE-Sim* enables them to use Python's powerful object-oriented features to manage multiple types of components in a complex system and multiple types of interactions between these components.
Second, by building upon Python, DE-Sim makes it easy for researchers to use Python's powerful data science tools, such as `NumPy <https://numpy.org/>`_, `Scipy <https://scipy.org/scipylib/index.html>`_, `pandas <https://pandas.pydata.org/>`_, and `SQLAlchemy <https://www.sqlalchemy.org/>`_,
to incorporate large, heterogeneous datasets into comprehensive and detailed models.
We anticipate that DE-Sim will enable a new generation of models that capture systems with unprecedented breadth and depth.

*DE-Sim* provides the following features which help users build and simulate complex, data-intensive models:

* **High-level, object-oriented modeling:** *DE-Sim* facilitates model designs that use classes of *simulation objects* to encapsulate the complex logic required to represent each *model component*, and use classes of *event messages* to encapsulate the logic required to describe their *interactions*.
* **Powerful stop conditions:** *DE-Sim* makes it easy to terminate simulations when specific criteria are reached. Modelers can specify stop conditions as functions that return true when the simulation should conclude.
* **Results checkpointing:** Models that use *DE-Sim* can simply record the results of simulations and metadata such as the start and run time of each simulation by configuring a checkpointing module.
* **Space-time visualizations:** *DE-Sim* can generate space-time visualizations of simulation trajectories. These diagrams can help researchers understand and debug simulations.
* **Reproducible simulations:** To help researchers debug simulations, repeated executions of a simulation with the same configuration and random number generator seed produce the same results.

*DE-Sim* has been used to develop `WC-Sim <https://github.com/KarrLab/wc_sim>`_, a multi-algorithmic simulator for `whole-cell models <https://www.wholecell.org>`_.

For more information, see the `interactive *DE-Sim* Jupyter notebooks <https://sandbox.karrlab.org/tree/de_sim>`_ that contain a *DE-Sim* tutorial and several example *DE-Sim* models.

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
   about.rst
