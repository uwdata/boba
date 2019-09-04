# -*- coding: utf-8 -*-

import os
import shutil
import csv
from dataclasses import dataclass
from .baseparser import ParseError


@dataclass
class Output:
    name: str
    value: str


exec_template = """\
#!/bin/sh

{}

DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" >/dev/null 2>&1 && pwd )"
prefix={}
suffix={}
num={}
i=1

while [ $i -le $num ]
do
  f="$DIR/$prefix$i$suffix"
  echo "{} $f"
  {} $f
  i=$(( i+1 ))
done

{}
"""

DIR_SCRIPT = 'code/'


class Wrangler:
    """Handles outputs."""
    def __init__(self, spec, lang, out):
        self.spec = spec
        self.lang = lang
        self.out = out
        self.fn = os.path.abspath(os.path.join(out, 'summary.csv'))

        self.outputs = {}
        self.col = 0
        self.counter = 0

        self.pre_exe = ''
        self.post_exe = ''

        self._read_spec()

    @staticmethod
    def _read_json_safe(obj, field):
        if field not in obj:
            raise ParseError('Cannot find "{}" in json'.format(field))
        return obj[field]

    @staticmethod
    def _read_optional(obj, field, df):
        return obj[field] if field in obj else df

    def _read_spec(self):
        """Read misc fields from the JSON spec."""
        sp = self._read_optional(self.spec, 'outputs', [])
        for d in sp:
            name = str(self._read_json_safe(d, 'name'))
            value = str(self._read_json_safe(d, 'value'))
            o = Output(name, value)
            self.outputs[name] = o

        self.pre_exe = self._read_optional(self.spec, 'before_execute', '')
        self.post_exe = self._read_optional(self.spec, 'after_execute', '')

    def _codegen_r(self):
        """Generate output code for R scripts."""
        if len(self.outputs) == 0:
            return ''

        # read csv
        code = '\n\n# wrangles output\n' \
            'df <- read.csv2("{}", sep = ",", stringsAsFactors = FALSE)'\
            .format(self.fn)

        # record outputs
        ns = self.get_outputs()
        col = self.col + 1
        row = self.counter
        for n in ns:
            code += '\ndf[{}, {}] = {}'.format(row, col, self.outputs[n].value)
            col += 1

        # write csv
        code += '\nwrite.csv(df, file="{}", row.names=FALSE)'.format(self.fn)
        code += '\n'

        return code

    def _codegen_python(self):
        if len(self.outputs) == 0:
            return ''

        # TODO

    def _gen_code(self):
        """Generate output code to be appended to the end of the script."""
        if self.lang.is_r():
            return self._codegen_r()
        if self.lang.is_python():
            return self._codegen_python()

    def write_sh(self):
        """Write a shell script for executing all universes."""
        cmd = self.lang.get_cmd()
        sh = exec_template.format(self.pre_exe,
                                  './{}universe_'.format(DIR_SCRIPT),
                                  self.lang.get_ext(), self.counter, cmd, cmd,
                                  self.post_exe)
        fn_exec = os.path.join(self.out, 'execute.sh')
        with open(fn_exec, 'w') as f:
            f.write(sh)
        st = os.stat(fn_exec)
        os.chmod(fn_exec, st.st_mode | 0o0111)

    def write_universe(self, code):
        """Write the generated code to a universe file."""

        self.counter += 1
        fn = 'universe_{}{}'.format(self.counter, self.lang.get_ext())

        # replace the reserved keyword _n
        code = code.replace('{{_n}}', str(self.counter))

        # append output code
        code += self._gen_code()

        # write file
        with open(os.path.join(self.out, DIR_SCRIPT, fn), 'w') as f:
            f.write(code)
            f.flush()

        return fn

    def write_csv(self, rows):
        """Write the summary CSV file"""
        with open(self.fn, 'w', newline='') as f:
            wrt = csv.writer(f)
            for row in rows:
                wrt.writerow(row)

    def create_dir(self):
        """Create output directories."""
        if os.path.exists(self.out):
            shutil.rmtree(self.out)
        os.makedirs(self.out)
        os.makedirs(os.path.join(self.out, DIR_SCRIPT))

    def get_outputs(self):
        """Get a sorted list of output names."""
        return sorted(list(self.outputs.keys()))
