# -*- coding: utf-8 -*-

import json
import os
from textwrap import wrap
from dataclasses import dataclass, field
from typing import List

from .blockparser import BlockParser, ParseError
from .graphparser import GraphParser, Edge
from .graphanalyzer import GraphAnalyzer, InvalidGraphError
from .decisionparser import DecisionParser
from .lang import LangError, Lang
from .wrangler import Wrangler
import boba.util as util


@dataclass
class Block:
    """
    A class for code blocks.

    id: unique identifier.
    parameter: parameter name, if the block is a decision.
    option: option name, if the block is a decision.
    chunks: code broken up at the boundaries of placeholder variables.
    """

    id: str = ''
    parameter: str = ''
    option: str = ''
    chunks: List = field(default_factory=lambda: [])


@dataclass
class Chunk:
    """A class for code chunks.
    A code chunk contains at most one placeholder variable.

    variable: the corresponding placeholder variable, if any.
    code: the code template proceeding the variable or the block boundary.
    """
    variable: str = ''
    code: str = ''


@dataclass
class History:
    """
    A class for keeping track of the choices made in each universe.

    path: index of the code path.
    filename: file name of the universe.
    decisions: placeholder variables and the options they took.
    """
    path: int
    filename: str = ''
    decisions: List = field(default_factory=lambda: [])


@dataclass
class DecRecord:
    """ A class for what options a parameter took. """
    parameter: str = ''
    option: str = ''
    idx: int = -1


class Parser:

    """ Parse everything """

    def __init__(self, f1, f2, out='.', lang=''):
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
        try:
            self.lang = Lang(lang, f1)
            self.wrangler = Wrangler(self.spec, self.lang, self.out)
        except LangError as e:
            self._throw(e.args[0])
        except ParseError as e:
            self._throw_spec_error(e.args[0])

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
        if block.id == '' and block.chunks[0].code == '':
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
        """ Make a pass over the template, parsing block declarations and
        placeholder variables inside the code."""

        try:
            self.dec_parser.read_decisions()
        except ParseError as e:
            self._throw_spec_error(e.args[0])

        with open(self.fn_script, 'r') as f:
            code = ''
            bl = Block()

            for line in f:
                if BlockParser.can_parse(line):
                    # end of the previous block
                    bl.chunks.append(Chunk('', code))
                    code = ''
                    self._add_block(bl)

                    # parse the metadata and create a new block
                    try:
                        bp_id, par, opt = BlockParser(line).parse()
                        bl = Block(bp_id, par, opt, [])
                    except ParseError as e:
                        self._throw_parse_error(e.args[0])
                else:
                    # match decision variables
                    try:
                        vs, codes = self.dec_parser.parse_code(line)
                        if len(vs):
                            # chop into more chunks
                            # combine first chunk with previous code
                            bl.chunks.append(Chunk(vs[0], code + codes[0]))
                            for i in range(1, len(vs)):
                                bl.chunks.append(Chunk(vs[i], codes[i]))

                            # remaining code after the last matched variable
                            code = codes[-1]
                        else:
                            code += line
                    except ParseError as e:
                        msg = 'At line "{}"\n\t{}'.format(line, e.args[0])
                        self._throw_parse_error(msg)

            # add the last block
            bl.chunks.append(Chunk('', code))
            self._add_block(bl)

    def _match_nodes(self, nodes):
        """ Nodes in spec and script should match. """
        blocks = set()
        for b in self.blocks:
            bl = self.blocks[b]
            blocks.add(bl.id if bl.parameter == '' else bl.parameter)

        for nd in nodes:
            if nd not in blocks:
                self._throw_spec_error('Cannot find matching node "{}" in script'.format(nd))

        for nd in blocks:
            # ignore special nodes inserted by us
            if not nd.startswith('_') and nd not in nodes:
                util.print_warn('Cannot find matching node "{}" in graph spec'.format(nd))

    def _replace_graph(self, nodes, edges):
        """ Replace the block-level decision nodes in the graph with option nodes."""

        # create a dict where key is the parameter and values are the options
        decs = {}
        for b in self.blocks:
            bl = self.blocks[b]
            if bl.parameter:
                p = bl.parameter
                if p in decs:
                    decs[p].append(bl.id)
                else:
                    decs[p] = [bl.id]

        # replace nodes
        nds = []
        for nd in nodes:
            tmp = decs[nd] if nd in decs else [nd]
            nds.extend(tmp)

        # replace edges
        egs = []
        for eg in edges:
            ss = decs[eg.start] if eg.start in decs else [eg.start]
            es = decs[eg.end] if eg.end in decs else [eg.end]
            egs.extend([Edge(s, e) for s in ss for e in es])

        return set(nds), set(egs)

    def _parse_graph(self):
        graph_spec = self.spec['graph'] if 'graph' in self.spec else []

        try:
            nodes, edges = GraphParser(graph_spec).parse()
            self._match_nodes(nodes)
            self.dec_parser.verify_naming(nodes)
            nodes, edges = self._replace_graph(nodes, edges)
            self.paths = GraphAnalyzer(nodes, edges).analyze()

            # an ugly way to handle the artificial _start node
            if '_start' in self.blocks:
                for p in self.paths:
                    p.insert(0, '_start')
                if len(self.paths) == 0:
                    self.paths = [['_start']]
        except ParseError as e:
            self._throw_spec_error(e.args[0])
        except InvalidGraphError as e:
            self._throw_spec_error(e.args[0])

    def _get_code_paths(self):
        """ Convert paths of block to paths of code chunk """

        res = []

        for path in self.paths:
            pt = []
            for nd in path:
                # replace the node by its chunks
                pt.extend(self.blocks[nd].chunks)
            res.append(pt)

        return res

    def _code_gen_recur(self, path, i, code, history):
        """
        Generate code recursively.

        :param path: the code path we're on.
        :param i: the index of the current node in the code path.
        :param code: the generated code so far.
        :param history: record the choices made.
        """

        if i >= len(path):
            # write file
            fn = self.wrangler.write_universe(code)

            # record history
            history.filename = fn
            self.history.append(history)
        else:
            chunk = path[i]

            if chunk.variable != '':
                # check if we have already encountered the placeholder variable
                prev_idx = None
                for d in history.decisions:
                    if d.parameter == chunk.variable:
                        prev_idx = d.idx

                if prev_idx is not None:
                    # use the previous value
                    snippet, opt = self.dec_parser.gen_code(chunk.code, chunk.variable, prev_idx)
                    self._code_gen_recur(path, i+1, code+snippet, history)
                else:
                    # expand the decision
                    num_alt = self.dec_parser.get_num_alt(chunk.variable)
                    for k in range(num_alt):
                        snippet, opt = self.dec_parser.gen_code(chunk.code, chunk.variable, k)
                        decs = [a for a in history.decisions]
                        decs.append(DecRecord(chunk.variable, opt, k))
                        self._code_gen_recur(path, i+1, code + snippet,
                                             History(history.path, '', decs))
            else:
                code += chunk.code
                self._code_gen_recur(path, i+1, code, history)

    def _code_gen(self):
        paths = self._get_code_paths()

        self.wrangler.counter = 0  # keep track of file name
        self.history = []          # keep track of choices made for each file
        self.wrangler.col = len(self.dec_parser.get_decs()) + 2

        self.wrangler.create_dir()
        for idx, p in enumerate(paths):
            self._code_gen_recur(p, 0, '', History(idx))

        # output a script to execute all universes
        self.wrangler.write_sh()

    @staticmethod
    def _nice_path(path):
        """ Convert the path containing block options back to the simpler path
         containing only block parameters."""
        ps = [p.split(':')[0] for p in path]
        decs = [DecRecord(p.split(':')[0], p.split(':')[1]) for p in path if ':' in p]
        return ps, decs

    def _write_csv(self):
        rows = []
        decs = self.dec_parser.get_decs() +\
            list(set(['({})'.format(b.parameter) for b in self.blocks.values()
                      if b.parameter != '']))
        ops = self.wrangler.get_outputs()
        rows.append(['Filename', 'Code Path'] + decs + ops)
        for h in self.history:
            paths, bdecs = self._nice_path(self.paths[h.path])
            row = [h.filename, '->'.join(paths)]
            mp = {}
            for d in h.decisions:
                mp[d.parameter] = d.option
            for d in bdecs:
                mp['({})'.format(d.parameter)] = d.option
            for d in decs:
                value = mp[d] if d in mp else ''
                row.append(value)
            rows.append(row)
        self.wrangler.write_csv(rows)

    def _print_summary(self):
        w = 80
        max_rows = 10

        print('=' * w)
        print('{:<20}{:<30}{:<30}'.format('Filename', 'Code Path', 'Decisions'))
        print('=' * w)
        for idx, h in enumerate(self.history):
            paths, bdecs = self._nice_path(self.paths[h.path])
            path = wrap('->'.join(paths), width=27)
            decs = ['{}={}'.format(d.parameter, d.option) for d in bdecs + h.decisions]
            decs = wrap(', '.join(decs), width=30)
            max_len = max(len(decs), len(path))

            for r in range(max_len):
                c1 = h.filename if r == 0 else ''
                c2 = path[r] if r < len(path) else ''
                c3 = decs[r] if r < len(decs) else ''

                print('{:<20}'.format(c1), end='')
                print('{:<30}'.format(c2), end='')
                print('{:<30}'.format(c3))
            print('-' * w)

            if idx >= max_rows - 1:
                print('... {} more rows'.format(len(self.history) - max_rows))
                break

    def main(self, verbose=True):
        self._parse_blocks()
        self._parse_graph()

        cap = self.dec_parser.get_cross_prod() * len(self.paths)
        if cap > 1024:
            rs = input('\nBoba may create as many as {} scripts. '
                       'Proceed (y/n)?\n'.format(cap))
            if not rs.strip().lower().startswith('y'):
                print('Aborted.')
                exit(0)

        self._code_gen()
        self._write_csv()
        if verbose:
            self._print_summary()
