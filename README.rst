====
boba
====

Author and execute multiverse analysis with ease.

Boba is a simple domain specific language for specifying multiverse analysis.
It comes with a command line tool to parse your specification and generate
universe scripts, allows you to execute all scripts with a single command, and
wrangles outputs into a single table.

- works with both python and R
- handles simple parameter substitution as well as complex code flow dependency

.. image:: https://badge.fury.io/py/boba.svg
  :target: https://badge.fury.io/py/boba
.. image:: https://travis-ci.org/uwdata/multiverse-spec.svg?branch=master
  :target: https://travis-ci.org/uwdata/multiverse-spec
.. image:: https://img.shields.io/badge/License-BSD%203--Clause-blue.svg
  :target: https://opensource.org/licenses/BSD-3-Clause)
.. image:: https://img.shields.io/pypi/pyversions/boba

Installation
============

You might download and install the latest version of this software from the
Python package index (PyPI)::

  pip install --upgrade boba

Usage
=====

To author your multiverse, please refer to the specification rules_.
Here is a `simple example`_ to get you started!


To parse your specification and generate actual scripts, invoke boba and pass
in the path to your template script and your JSON spec::

  boba --script template.py -- json spec.json

For more command line options, see `CLI`_.

.. _rules: https://github.com/uwdata/multiverse-spec/blob/master/tutorial/rules.md
.. _simple example: https://github.com/uwdata/multiverse-spec/blob/master/tutorial/simple.md
.. _more complex example: https://github.com/uwdata/multiverse-spec/blob/master/tutorial/fertility.md

CLI
===

You might invoke the command line tool via::
  boba [options]

It has a few simple options:

``--script, -s``
  **default: ./script_annotated.py** (optional)

  The path to your template script.

``--json, -j``
  **default: ./spec.json** (optional)

  The path to your JSON specification.

``--out, -o``
  **default: .** (optional)

  The output directory to hold generated universe scripts, summary table, etc.

``--lang, -l``
  (optional)

  Language of your analysis script; we support python and R at the moment.
  If not specified, we will infer it from the file extension.

``--help``
  Show help message and exit.

Examples
========

- A `simple example`_ to walk you through the basics
- A `more complex example`_ using `Steegen's_ multiverse analysis`_ and `Durante's fertility dataset`_.
- Another multiverse analysis_ applied to a `reading speed dataset`_ collected by Qisheng Li et al.

.. _reading speed dataset: https://github.com/QishengLi/CHI2019_Reader_View
.. _analysis: https://github.com/uwdata/multiverse-spec/tree/master/example/reading
.. _Steegen's_ multiverse analysis: https://journals.sagepub.com/doi/pdf/10.1177/1745691616658637
.. _Durante's fertility dataset: https://osf.io/zj68b/
