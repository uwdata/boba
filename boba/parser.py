# -*- coding: utf-8 -*-

import json
import os
from textwrap import wrap
from dataclasses import dataclass, field
from typing import List

from .baseparser import ParseError
from .codeparser import CodeParser
from .graphparser import GraphParser, Edge
from .graphanalyzer import GraphAnalyzer, InvalidGraphError
from .decisionparser import DecisionParser
from .constraintparser import ConstraintParser
from .lang import LangError, Lang
from .wrangler import Wrangler
import boba.util as util


@dataclass
class History:
    """
    A class for keeping track of the choices made in each universe.

    path: index of the code path.
    filename: file name of the universe.
    decisions: placeholder variables and the options they took.
    skipped: nodes that are skipped.
    """
    path: int
    filename: str = ''
    decisions: List = field(default_factory=lambda: [])
    skipped: List = field(default_factory=lambda: [])


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

        self.paths = []
        self.history = []
        self.constraints = {}

        # read spec
        with open(f2, 'rb') as f:
            self.spec = json.load(f)

        # initialize helper class
        self.dec_parser = DecisionParser(self.spec)
        self.code_parser = CodeParser()
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

    def _parse_blocks(self):
        """ Make a pass over the template, parsing block declarations and
        placeholder variables inside the code."""
        try:
            self.dec_parser.read_decisions()
        except ParseError as e:
            self._throw_spec_error(e.args[0])

        with open(self.fn_script, 'r') as f:
            try:
                self.code_parser.parse(self.dec_parser, f)
            except ParseError as e:
                self._throw_parse_error(e.args[0])

    def _match_nodes(self, nodes):
        """ Nodes in spec and script should match. """
        blocks = self.code_parser.get_block_names()

        for nd in nodes:
            if nd not in blocks:
                self._throw_spec_error('Cannot find matching node "{}" in script'.format(nd))

        for nd in blocks:
            # ignore special nodes inserted by us
            if not nd.startswith('_') and nd not in nodes:
                util.print_warn('Cannot find matching node "{}" in graph spec'.format(nd))

    def _replace_graph(self, nodes, edges):
        """ Replace the block-level decision nodes in the graph with option nodes."""
        decs = self.code_parser.get_decisions()

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
            gp = GraphParser(graph_spec)
            nodes, edges = gp.parse()

            # if the user didn't specify the graph, use default
            if len(nodes) == 0:
                nodes, edges = gp.create_default_graph(self.code_parser.order)

            # check if graph nodes matches block IDs, and vice versa
            self._match_nodes(nodes)
            # check if any name of nodes collides with variable names
            self.dec_parser.verify_naming(nodes)
            # expand the graph with options
            nodes, edges = self._replace_graph(nodes, edges)

            # analyze the graph to get paths
            self.paths = GraphAnalyzer(nodes, edges).analyze()
            # an ugly way to handle the artificial _start node
            if '_start' in self.code_parser.blocks and '_start' not in nodes:
                for p in self.paths:
                    p.insert(0, '_start')
                if len(self.paths) == 0:
                    self.paths = [['_start']]
        except ParseError as e:
            self._throw_spec_error(e.args[0])
        except InvalidGraphError as e:
            self._throw_spec_error(e.args[0])

    def _parse_constraints(self):
        try:
            self.constraints = ConstraintParser(self.spec)\
                .read_constraints(self.code_parser, self.dec_parser)
        except ParseError as e:
            self._throw_spec_error(e.args[0])

    def _eval_constraint(self, history, con):
        """ See if the constraint holds true given the choices made. """
        con = self.constraints[con].condition
        paths, bdecs = self._nice_path(self._get_skipped_path(history))

        # A dict where the key is each parameter and the value is the chosen
        # option. For ordinary blocks, key and value are the same.
        res = {}
        for p in paths:
            res[p] = p
        for d in bdecs:
            # note that block parameter will override with the actual option
            res[d.parameter] = d.option
        for d in self.dec_parser.get_decs():
            # unmade decisions will have value None and index -1
            res[d] = None
            res[ConstraintParser.make_index_var(d)] = -1
        for d in history.decisions:
            res[d.parameter] = d.option
            res[ConstraintParser.make_index_var(d.parameter)] = d.idx

        # now evaluate
        return eval(con, res)

    def _get_code_paths(self):
        """ Convert paths of block to paths of code chunk """

        res = []

        for path in self.paths:
            pt = []
            for nd in path:
                # replace the node by its chunks
                chunks = [(nd, ch) for ch in self.code_parser.blocks[nd].chunks]
                pt.extend(chunks)
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
            nd, chunk = path[i]

            # check if the block has constraints attached to it
            names = [nd, nd.split(':')[0]]
            for n in names:
                if n in self.constraints and\
                        not self._eval_constraint(history, n):
                    # constraint met
                    if self.constraints[n].skip:
                        # skip the node and continue
                        history.skipped.append(nd)
                        self._code_gen_recur(path, i + 1, code, history)
                        return
                    else:
                        # abort codegen
                        return

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
                        # check if the option has constraints attached to it
                        v = self.dec_parser.get_alt(chunk.variable, k)
                        v = '{}:{}'.format(chunk.variable, v)
                        if v in self.constraints and \
                                not self._eval_constraint(history, v):
                            # constraint met, abort
                            continue

                        # code gen
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

    def _get_skipped_path(self, h):
        """ Get the history's path, with skipped nodes removed. """
        sk = set(h.skipped)
        return [nd for nd in self.paths[h.path] if nd not in sk]

    def _write_csv(self):
        rows = []
        decs = self.dec_parser.get_decs() +\
            ['({})'.format(b) for b in self.code_parser.get_decisions()]
        ops = self.wrangler.get_outputs()
        rows.append(['Filename', 'Code Path'] + decs + ops)
        for h in self.history:
            paths, bdecs = self._nice_path(self._get_skipped_path(h))
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
            paths, bdecs = self._nice_path(self._get_skipped_path(h))
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

    def _warn_size(self):
        cap = self.dec_parser.get_cross_prod() * len(self.paths)
        if cap > 1024:
            rs = input('\nBoba may create as many as {} scripts. '
                       'Proceed (y/n)?\n'.format(cap))
            if not rs.strip().lower().startswith('y'):
                print('Aborted.')
                exit(0)

    def main(self, verbose=True):
        self._parse_blocks()
        self._parse_graph()
        self._parse_constraints()

        self._warn_size()
        self._code_gen()
        self._write_csv()
        if verbose:
            self._print_summary()
