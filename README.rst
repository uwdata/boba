====
boba
====

Author and visualize multiverse analysis with ease.

Boba has a domain specific language (Boba DSL) for writing multiverse specifications,
and a visual analysis interface (`Boba Visualizer`_) for exploring multiverse outcomes.
Boba comes with a command line tool to parse your DSL specification and generate
universe scripts, execute all scripts with a single command,
merges outputs into a table, and invoke the visualizer.

- works with both python and R, and other scripting languages to come
- handles simple parameter substitution as well as complex code flow dependency
- offers interactive visualizations for exploring consequential decisions, uncertainty, model fit, and more

.. _Boba Visualizer: https://github.com/uwdata/boba-visualizer
.. image:: https://badge.fury.io/py/boba.svg
  :target: https://badge.fury.io/py/boba
.. image:: https://travis-ci.org/uwdata/boba.svg?branch=master
  :target: https://travis-ci.org/uwdata/boba
.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
  :target: https://opensource.org/licenses/BSD-3-Clause)
.. image:: https://img.shields.io/pypi/pyversions/boba

Installation
============

You might download and install the latest version of this software from the
Python package index (PyPI)::

  pip install --upgrade boba
  pip install --upgrade boba-visualizer

Usage
=====

To author your multiverse, please refer to the specification rules_.
Here is a `simple example`_ to get you started!


To parse your specification and generate actual scripts, invoke boba and pass
in the path to your template script and your JSON spec::

  boba compile --script template.py

To execute the multiverse, namely running all the generated scripts, use::

  boba run --all

To start the Boba Visualizer after getting the intermediate output files, use::

  boba-server

For more command line options, see `CLI`_.
For more information about the Boba Visualizer, see this project_.

.. _rules: https://github.com/uwdata/boba/blob/master/tutorial/rules.md
.. _simple example: https://github.com/uwdata/boba/blob/master/tutorial/simple.md
.. _more complex example: https://github.com/uwdata/boba/blob/master/tutorial/fertility.md
.. _CLI: https://github.com/uwdata/boba/blob/master/tutorial/cli.rst
.. _project: https://github.com/uwdata/boba-visualizer

Examples
========

- A `simple example`_ to walk you through the basics
- A `more complex example`_ using `Steegen's multiverse analysis`_ and `Durante's fertility dataset`_.
- Another multiverse example_, based on the `specification curve paper`_ by Simonsohn et al.

.. _reading speed dataset: https://github.com/QishengLi/CHI2019_Reader_View
.. _analysis: https://github.com/uwdata/boba/tree/master/example/reading
.. _example: https://github.com/uwdata/boba/tree/master/example/hurricane
.. _specification curve paper: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2694998
.. _Steegen's multiverse analysis: https://journals.sagepub.com/doi/pdf/10.1177/1745691616658637
.. _Durante's fertility dataset: https://osf.io/zj68b/

Citation
========

If you are interested in this work, please see our research paper_ and consider citing our work::

  @misc{liu2020boba,
    title={Boba: Authoring and visualizing multiverse analyses},
    author={Yang Liu and Alex Kale and Tim Althoff and Jeffrey Heer},
    year={2020},
    eprint={2007.05551},
    archivePrefix={arXiv},
    primaryClass={cs.HC}
  }

.. _paper: https://arxiv.org/abs/2007.05551