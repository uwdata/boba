# -*- coding: utf-8 -*-

import json
from dataclasses import dataclass
from .baseparser import ParseError
from .conditionparser import ConditionParser, TokenType


@dataclass
class Constraint:
    block: str = ''
    variable: str = ''
    option: str = ''
    index: int = -1
    skip: bool = False
    condition: str = ''


class ConstraintParser:
    def __init__(self, spec):
        self.spec = spec
        self.constraints = {}

        # useful for inferring ADGs
        self.links = []
        self.procedural = set()

    @staticmethod
    def _read_required(obj, field):
        if field not in obj:
            msg = 'Cannot find required field "{}"'.format(field)
            ConstraintParser._throw(msg, obj)
        return obj[field]

    @staticmethod
    def _read_optional(obj, field, df=None):
        return obj[field] if field in obj else df

    @staticmethod
    def _throw(msg, c):
        raise ParseError('In parsing constraints:\n\t' + json.dumps(c)
                         + '\n\t\t' + msg)

    @staticmethod
    def make_index_var(w):
        """ Embellish the variable name if the user is checking the option
         by its index in the options array."""
        return '_i_' + w

    @staticmethod
    def _verify_block(block, blocks, constraint):
        """ Check if a block is defined in the template script. """
        if block is not None and block not in blocks:
            msg = 'Block "{}" does not match any existing block ID'
            ConstraintParser._throw(msg.format(block), constraint)

    @staticmethod
    def _verify_placeholder_var(v, decs, constraint):
        """ Check if a placeholder variable is declared in decisions. """
        if v is not None and v not in decs:
            msg = 'Variable "{}" does not match any existing variable'
            ConstraintParser._throw(msg.format(v), constraint)

    @staticmethod
    def _verify_var_option(v, opt, decs, constraint):
        """ Check if an option to a placeholder variable exists. """
        opts = [str(o) for o in decs[v].value]
        if str(opt) not in opts:
            msg = 'Variable "{}" has no option "{}"'
            ConstraintParser._throw(msg.format(v, opt), constraint)

    @staticmethod
    def _verify_block_option(block, opt, bl_decs, constraint):
        """ Check if an option to a block exists."""
        if '{}:{}'.format(block, opt) not in bl_decs[block]:
            msg = 'Block "{}" has no option "{}"'
            ConstraintParser._throw(msg.format(block, opt), constraint)

    @staticmethod
    def _verify_option(param, block, opt, decs, bl_decs, c):
        """ Check if an option exists. """
        if opt is not None and param:
            ConstraintParser._verify_var_option(param, opt, decs, c)
        if opt is not None and block:
            ConstraintParser._verify_block_option(block, opt, bl_decs, c)

    @staticmethod
    def _verify_index(v, idx, decs, constraint):
        """ Check if the index of a placeholder variable is valid. """
        if idx is not None and (idx < 0 or idx >= len(decs[v].value)):
            msg = 'Index {} is out of range for variable "{}"'
            ConstraintParser._throw(msg.format(idx, v), constraint)

    @staticmethod
    def _verify_link(link, decs, bl_decs, constraint):
        """ Check if the linked decisions exist and have the same size """
        m = 0
        for l in link:
            if l not in decs and l not in bl_decs:
                msg = 'Decision "{}" not found'
                ConstraintParser._throw(msg.format(l), constraint)
            n = len(decs[l].value) if l in decs else len(bl_decs[l])
            if m != 0 and n != m:
                msg = 'Linked decisions must have the same number of options'
                ConstraintParser._throw(msg, constraint)
            m = n

    @staticmethod
    def _convert_link(link, decs, bl_decs):
        """ Convert linked decisions to constraints """
        res = []
        ls = []
        size = 0

        # first, turn variable/block decisions into a shared format
        for l in link:
            tp = 'variable' if l in decs else 'block'
            opt = decs[l].value if l in decs \
                else list(map(lambda x: x.split(':')[1], bl_decs[l]))
            ls.append({'type': tp, 'name': l, 'options': opt})
            size = len(opt)

        # then, construct pairwise dependencies
        for i in range(size):
            for l in ls:
                cond = ''
                for j in ls:
                    if j != l:
                        if j['type'] == 'variable':
                            cond += ' and ({}.index < 0 or {}.index == {})'\
                                .format(j['name'], j['name'], i)
                        else:
                            cond += ' and {} == {}'.format(j['name'], j['options'][i])
                cs = {l['type']: l['name'], 'condition': cond[5:], '_source': 'link'}
                if l['type'] == 'block':
                    cs['option'] = l['options'][i]
                else:
                    cs['index'] = i
                res.append(cs)
        return res

    @staticmethod
    def _verify_json_syntax(block, param, opt, constraint, idx):
        """ Check if the json has the correct combination of fields. """
        if block is not None and param is not None:
            msg = 'Cannot handle variable and block at the same line.'
            ConstraintParser._throw(msg, constraint)

        if opt is not None:
            if param is None and block is None:
                msg = 'No corresponding variable/block for option "{}"'
                ConstraintParser._throw(msg.format(opt), constraint)

        if param is not None:
            if opt is None and idx is None:
                msg = 'Must specify option/index for a variable.'
                ConstraintParser._throw(msg, constraint)

    @staticmethod
    def _verify_condition_vars(parsed, decs, blocks, constraint):
        """ Check if the variables and blocks in the condition exist. """
        for i, p in enumerate(parsed):
            if i % 2 == 1:
                # skipping the rhs
                continue

            # see if it matches anything from decs and blocks
            pv = p.value
            if pv not in decs and pv not in blocks:
                msg = '"{}" does not match any block or variable'.format(pv)
                ConstraintParser._throw(msg, constraint)

    @staticmethod
    def _maybe_get_index(param, opt, idx, decs):
        """ Placeholder's option is always checked by index. """
        if not param:
            return -1
        if idx is not None:
            return idx
        for i, o in enumerate(decs[param].value):
            if str(o) == str(opt):
                return i

    @staticmethod
    def _create_key(c):
        if c.block:
            key = '{}:{}'.format(c.block, c.option) if c.option else c.block
        else:
            v = ConstraintParser.make_index_var(c.variable)
            key = '{}:{}'.format(v, c.index)
        return key

    def _recon(self, code, parsed_decs, cond):
        """ Transform parsed code and decisions into valid python code """
        exe = []
        for i, d in enumerate(parsed_decs):
            if d.type == TokenType.index_var:
                exe.append(self.make_index_var(d.value))
            elif i % 2 == 1 and parsed_decs[i - 1].type == TokenType.var:
                # wrap any RHS in quotes, except for indices
                # because the history class represent any option as strings
                exe.append('"{}"'.format(d.value))
            else:
                exe.append(d.value)

        recon = code.format(*exe)

        # check if the code has syntax error
        try:
            eval(recon, {})
        except SyntaxError:
            msg = 'In parsing condition:\n\t' + cond + \
                  '\nSyntax Error: invalid syntax'
            raise ParseError(msg)
        except NameError:
            pass

        return recon

    def _infer_procedural_deps(self, c, block, variable, cond):
        """ Infer procedural edges from parsed condition """
        # skip constraints added by us, for example links
        if '_source' not in c:
            dec = block if block else variable
            # current node should depend on all decisions on the LHS
            for i in range(0, len(cond), 2):
                v = cond[i].value
                self.procedural.add('{}-{}'.format(v, dec))

    def read_constraints(self, code_parser, dec_parser):
        """ Read the constraints from the JSON spec. """
        cons = ConstraintParser._read_optional(self.spec, 'constraints', [])

        decs = dec_parser.decisions
        bls = code_parser.get_block_names()
        bl_decs = code_parser.get_decisions()

        # first separate links and conditions
        pure_cons = []
        for c in cons:
            # read link
            link = ConstraintParser._read_optional(c, 'link')
            if link:
                ConstraintParser._verify_link(link, decs, bl_decs, c)
                self.links.append(link)
                pure_cons += ConstraintParser._convert_link(link, decs, bl_decs)
            else:
                pure_cons.append(c)

        # add inline constraints
        pure_cons += code_parser.inline_constraints

        # then parse all conditions, including generated ones from link
        for c in pure_cons:
            # read block
            block = ConstraintParser._read_optional(c, 'block')
            ConstraintParser._verify_block(block, bls, c)

            # read variable
            param = ConstraintParser._read_optional(c, 'variable')
            ConstraintParser._verify_placeholder_var(param, decs, c)

            # read skip flag
            skip = bool(ConstraintParser._read_optional(c, 'skippable'))

            # read index
            idx = ConstraintParser._read_optional(c, 'index')
            ConstraintParser._verify_index(param, idx, decs, c)

            # read option
            opt = ConstraintParser._read_optional(c, 'option')
            ConstraintParser._verify_option(param, block, opt, decs, bl_decs, c)

            # verify everything and convert option to index for placeholder
            ConstraintParser._verify_json_syntax(block, param, opt, c, idx)
            idx = ConstraintParser._maybe_get_index(param, opt, idx, decs)

            # read condition
            cond = ConstraintParser._read_required(c, 'condition')
            code, parsed_decs = ConditionParser(cond).parse()
            if len(parsed_decs) % 2 == 1:
                ConstraintParser._throw('Binary operator expected', c)
            ConstraintParser._verify_condition_vars(parsed_decs, decs, bls, c)

            # get procedural dependency
            self._infer_procedural_deps(c, block, param, parsed_decs)

            # now transform it into valid python code
            recon = self._recon(code, parsed_decs, cond)

            # save
            constraint = Constraint(block, param, opt, idx, skip, recon)
            key = ConstraintParser._create_key(constraint)
            self.constraints[key] = constraint

        return self.constraints
