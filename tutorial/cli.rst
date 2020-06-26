===
CLI
===

You might invoke the command line tool via::
  boba <command> [options]

Available commands:
 - compile
 - run

General options:

``--version``
  Show version and exit.

Compile
=======
The compile command parses the template script and the JSON spec to generate
executable universe scripts. It has the following options:

``--script, -s``
  **default: ./template.py** (optional)

  The path to your template script.

``--json, -j``
  **default: ./spec.json** (optional)

  The path to your JSON specification.

``--out``
  **default: .** (optional)

  The output directory to hold generated universe scripts, summary table, etc.

``--lang``
  (optional)

  Language of your analysis script; we support python and R at the moment.
  If not specified, we will infer it from the file extension.

``--help``
  Show help message and exit.

Run
===
The run command executes the generated universe scripts. You could use it to
run the entire multiverse, a single universe, or a subset of universes. To run
all universes, use::

  boba run --all

To run a single universe, provide its identifying number as the argument. For
example, if you want to run universe_1.py, use::

  boba run 1

To run a range of universes, for example universe_1 through universe_5, use::

  boba run 1 --thru 5

The following two parameters are for multiprocessing:

``--jobs``
  **default: 1 (optional)**

  Determines the number of processes that can run at a time. If *jobs* is set to 0, it becomes the number of cores on the machine.

``--batch_size``
  **default: see below (optional)**

  Determines the number of universes that will be run in a sequence in each process. Let :math:`N` denotes the number of universes, the default is :math:`sqrt(N)` or :math:`N/jobs + 1`, whichever is smaller.