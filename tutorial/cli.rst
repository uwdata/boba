===
CLI
===

You might invoke the command line tool via::
  boba <command> [options]

Available commands:
 - compile
 - run
 - merge

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

``--out``
  **default: .** (optional)

  The output directory to hold generated universe scripts, summary table, etc.

``--lang``
  (optional)

  Language of your analysis script. We support python and R, and require a
  configuration file for any other languages.
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

In addition, the run command accepts the following options:

``--dir``
  **default: ./multiverse (optional)**

  Determines the path to the multiverse directory. It should point to a directory
  that contains the *summary.csv* file and the *code* subfolder.

``--jobs``
  **default: 1 (optional)**

  Determines the number of processes that can run at a time. If *jobs* is set
  to 0, it becomes the number of cores on the machine.

``--batch_size``
  **default: see below (optional)**

  Determines the number of universes that will be run in a sequence in each
  process. Let :math:`N` denotes the number of universes, the default is
  :math:`sqrt(N)` or :math:`N/jobs + 1`, whichever is smaller.

Merge
=====
The merge command combines CSV outputs from individual universes into one file.
This command works well if you used the built-in `{{_n}}` variable to output
a separate CSV per universe.

The command has a required argument: the filename pattern of individual outputs
where the universe id is replaced by {}. For example, if your output
files are output_1.csv, output_2.csv, output_3.csv, and so on, your pattern
should be `output_{}.csv`.

In addition, the command has the following options:

``--base, -b``
  **default: ./multiverse/results (optional)**

  Path to the directory containing the universe outputs.

``--out``
  **default: ./multiverse/merged.csv (optional)**

  Path to the merged file that will be created by this command.

``--delimiter``
  **default: , (optional)**

  CSV delimiter.
