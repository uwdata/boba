===
CLI
===

You might invoke the command line tool via::
  boba <command> [options]

Available commands:
 - compile

General options:

``--version``
  Show version and exit.

Compile
=======
The compile command has the following options:

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
