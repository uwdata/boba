#!/usr/bin/env python3

import json
import os
import shutil
import csv
from dataclasses import dataclass, field
from typing import List

from src.blockparser import BlockParser, ParseError
from src.graphparser import GraphParser
from src.graphanalyzer import GraphAnalyzer, InvalidGraphError
from src.decisionparser import DecisionParser
import src.util as util


@dataclass
class Block:
    code: str = ''
    id: str = ''
    name: str = ''
    chunks: List = field(default_factory=lambda: [])


@dataclass
class History:
    path: int
    filename: str = ''
    decisions: List = field(default_factory=lambda: [])


class Parser:

    """ Parse everything """

    def __init__(self, f1, f2, out='.'):
        self.fn_script = f1
        self.fn_spec = f2
        self.out = os.path.join(out, 'multiverse/')

        self.blocks = {}
        self.paths = []
        self.history = []

        # read spec
        with open(f2, 'rb') as f:
            self.spec = json.load(f)

        # initialize helper class
        self.dec_parser = DecisionParser(self.spec)

    def _throw(self, msg):
        util.print_fail(msg)
        exit(1)

    def _indent(self, msg):
        return '\n'.join(['\t' + l for l in msg.split('\n')])

    @staticmethod
    def _rename_dec(dec):
        return '_' + dec

    def _throw_parse_error(self, msg):
        prefix = 'In parsing file "{}":\n'.format(self.fn_script)
        self._throw(prefix + self._indent(msg))

    def _throw_spec_error(self, msg):
        prefix = 'In parsing file "{}":\n'.format(self.fn_spec)
        self._throw(prefix + self._indent(msg))

    def _add_block(self, block):
        # ignore empty block
        if block.id == '' and block.code == '':
            return

        # handle unnamed block
        if block.id == '':
            block.id = '_start' if len(self.blocks) == 0 else '_end'

        # check if id exists
        if block.id in self.blocks:
            err = 'Duplicated code block ID "{}"'.format(block.id)
            self._throw_parse_error(err)
        self.blocks[block.id] = block

    def _parse_blocks(self):
        try:
            self.dec_parser.read_decisions()
        except ParseError as e:
            self._throw_spec_error(e.args[0])

        with open(self.fn_script, 'r') as f:
            code = ''
            bl = Block()

            for line in f:
                if BlockParser.can_parse(line):
                    # end of the last block
                    bl.chunks.append(('', code))
                    code = ''
                    self._add_block(bl)

                    # parse the metadata and create a new block
                    try:
                        bp_id, bp_name = BlockParser(line).parse()
                        bl = Block('', bp_id, bp_name, [])
                    except ParseError as e:
                        self._throw_parse_error(e.args[0])
                else:
                    # match decision variables
                    try:
                        vs, codes = self.dec_parser.parse_code(line)
                        if len(vs):
                            # chop into more chunks
                            # combine first chunk with previous code
                            bl.chunks.append((vs[0], code + codes[0]))
                            for i in range(1, len(vs)):
                                bl.chunks.append((vs[i], codes[i]))

                            # remaining code after the last matched variable
                            code = codes[-1]
                        else:
                            code += line
                    except ParseError as e:
                        msg = 'At line "{}"\n\t{}'.format(line, e.args[0])
                        self._throw_parse_error(msg)

                    # TODO: fix legacy
                    bl.code += line

            # add the last block
            bl.chunks.append(('', code))
            self._add_block(bl)

    def _match_nodes(self, nodes):
        # nodes in spec and script should match
        for nd in nodes:
            if nd not in self.blocks:
                self._throw_spec_error('Cannot find matching node "{}" in script'.format(nd))

        for nd in self.blocks:
            # ignore special nodes inserted by us
            if not nd.startswith('_') and nd not in nodes:
                util.print_warn('Cannot find matching node "{}" in graph spec'.format(nd))

    def _parse_graph(self):
        if 'graph' not in self.spec:
            self._throw_spec_error('Cannot find "graph" in json')

        try:
            nodes, edges = GraphParser(self.spec['graph']).parse()
            self._match_nodes(nodes)
            self.paths = GraphAnalyzer(nodes, edges).analyze()
        except ParseError as e:
            self._throw_spec_error(e.args[0])
        except InvalidGraphError as e:
            self._throw_spec_error(e.args[0])

    def _get_code_paths(self):
        res = []

        for path in self.paths:
            pt = []
            for nd in path:
                pt.extend(self.blocks[nd].chunks)
            res.append(pt)

        return res

    def _code_gen_recur(self, path, i, code, history):
        if i >= len(path):
            self.counter += 1
            fn = 'universe_{}.py'.format(self.counter)

            # record history
            tks = history.split('\n')
            self.history.append(History(int(tks[0]), fn, tks[1:]))

            # prepend _start to every file
            if '_start' in self.blocks:
                code = self.blocks['_start'].code + code

            # write file
            fn = os.path.join(self.out, 'codes/', fn)
            with open(fn, 'w') as f:
                f.write(code)
                f.flush()
        else:
            val, template = path[i]

            if val != '':
                # expand the decision
                num_alt = self.dec_parser.get_num_alt(val)
                for k in range(num_alt):
                    snippet, opt = self.dec_parser.gen_code(template, val, k)
                    self._code_gen_recur(path, i+1, code + snippet,
                                         '{}\n{}={}'.format(history, val, opt))
            else:
                code += template
                self._code_gen_recur(path, i+1, code, history)

    def _code_gen(self):
        if os.path.exists(self.out):
            shutil.rmtree(self.out)
        os.makedirs(self.out)
        os.makedirs(os.path.join(self.out, 'codes/'))

        paths = self._get_code_paths()

        self.counter = 0    # keep track of file name
        self.history = []   # keep track of choices made for each file
        for idx, p in enumerate(paths):
            self._code_gen_recur(p, 0, '', str(idx))

        # TODO: output a script to execute all universes

    def _write_csv(self):
        with open(os.path.join(self.out, 'summary.csv'), 'w', newline='') as f:
            wrt = csv.writer(f)
            decs = [i for i in self.dec_parser.decisions.keys()]
            wrt.writerow(['Filename', 'Code Path'] + decs)
            for h in self.history:
                row = [h.filename, '->'.join(self.paths[h.path])]
                mp = {}
                for d in h.decisions:
                    tks = d.split('=')
                    mp[tks[0]] = tks[1]
                for d in decs:
                    row.append(mp[d])
                wrt.writerow(row)

    def _print_summary(self):
        w = 80

        print('-' * w)
        print('{:<20}{:<20}{:<40}'.format('Filename', 'Code Path', 'Decisions'))
        print('-' * w)
        for h in self.history:
            print('{:<20}'.format(h.filename), end='')
            print('{:<20}'.format('->'.join(self.paths[h.path])), end='')
            print('{:<40}'.format(', '.join(h.decisions)))
        print('-' * w)

    def main(self):
        self._parse_blocks()
        self._parse_graph()
        self._code_gen()
        self._write_csv()
        self._print_summary()
