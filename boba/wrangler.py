# -*- coding: utf-8 -*-

import os
import shutil
import csv
import json
from dataclasses import dataclass
from .baseparser import ParseError


@dataclass
class Output:
    name: str
    value: str


exec_template = """\
#!/bin/sh

cleanup ()
{{
echo "kill -s TERM $!"
kill -s TERM $!
exit 0
}}

merge_log ()
{{
boba merge exit_status_{{}}.csv -b $DLOG --out $DLOG/exit_status.csv
rm $DLOG/exit_status_*.csv
}}

{}

DIR="$( cd "$( dirname "${{BASH_SOURCE[0]}}" )" >/dev/null 2>&1 && pwd )"
DLOG=$DIR/boba_logs
suffix={}
num={}
i=1

# create a folder for logs
rm -rf $DLOG
mkdir $DLOG

# if specified, change the range of universes to execute
if [ "$1" != "" ]; then i=$1; num=$1; fi
if [ "$2" != "" ]; then num=$2; fi

cd $DIR/code

trap cleanup SIGINT SIGTERM

while [ $i -le $num ]
do
  # execute the universe
  f="universe_$i$suffix"
  echo "{} $f"
  (set -o pipefail; {} $f 2>&1 | tee $DLOG/log_$i.txt)

  # collect exit status
  printf "%s\\n%d" exit_status $? > $DLOG/exit_status_$i.csv

  # increment
  i=$(( i+1 ))
  wait $!
done

merge_log
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
        self.col = 0  # output column number, will be set by parser
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
            'df <- read.csv2("{}", sep = ",", stringsAsFactors = FALSE, ' \
               'check.names=FALSE)'\
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
                                  self.lang.get_ext(), self.counter, cmd, cmd,
                                  self.post_exe)
        fn_exec = os.path.join(self.out, 'execute.sh')
        with open(fn_exec, 'w') as f:
            f.write(sh)
        st = os.stat(fn_exec)
        os.chmod(fn_exec, st.st_mode | 0o0111)

    def write_pre_exe(self):
        fn_pre_exec = os.path.join(self.out, 'pre_exe')
        with open(fn_pre_exec, 'w') as f:
            f.write(self.pre_exe)
    
    def write_post_exe(self):
        fn_post_exec = os.path.join(self.out, 'post_exe')
        with open(fn_post_exec, 'w') as f:
            f.write(self.post_exe)

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

    def write_summary(self, rows):
        """Write the summary CSV file"""
        with open(self.fn, 'w', newline='') as f:
            wrt = csv.writer(f)
            for row in rows:
                wrt.writerow(row)

    def write_overview_json(self, res):
        """ Write the overview.json file"""
        # append visualizer block
        default_config = {
            "files": [{"id": "est", "path": "estimates.csv"}],
            "schema": {"point_estimate": {"file": "est", "field": "estimate"}}
        }
        vis = Wrangler._read_optional(self.spec, 'visualizer', None)

        # if it is a string, read config file
        if isinstance(vis, str):
            try:
                with open(vis) as f:
                    vis = json.load(f)
            except (IOError, json.JSONDecodeError) as e:
                print(e)
                print('Cannot read the visualizer config, using the default')
                vis = default_config
        # if user does not specify the config, use the default
        vis = default_config if vis is None else vis
        res['visualizer'] = vis

        with open(os.path.join(self.out, 'overview.json'), 'w') as f:
            obj = json.dumps(res, indent=2, sort_keys=True)
            f.write(obj)

    def create_dir(self):
        """Create output directories."""
        if os.path.exists(self.out):
            shutil.rmtree(self.out)
        os.makedirs(self.out)
        os.makedirs(os.path.join(self.out, DIR_SCRIPT))

    def get_outputs(self):
        """Get a sorted list of output names."""
        return sorted(list(self.outputs.keys()))
