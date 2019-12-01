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
    skip: bool = False
    condition: str = ''


class ConstraintParser:
    def __init__(self, spec):
        self.spec = spec
        self.constraints = {}

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
    def _verify_json_syntax(block, param, opt, constraint):
        """ Check if the json has the correct combination of fields. """
        if block is not None and param is not None:
            msg = 'Cannot handle variable and block at the same line.'
            ConstraintParser._throw(msg, constraint)

        if opt:
            if param is None and block is None:
                msg = 'No corresponding variable/block for option "{}"'
                ConstraintParser._throw(msg.format(opt), constraint)
        elif param is not None:
            msg = 'Must specify option for a variable.'
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

    def read_constraints(self, code_parser, dec_parser):
        """ Read the constraints from the JSON spec. """
        cons = ConstraintParser._read_optional(self.spec, 'constraints', [])

        decs = dec_parser.decisions
        bls = code_parser.get_block_names()
        bl_decs = code_parser.get_decisions()

        for c in cons:
            # read block
            block = ConstraintParser._read_optional(c, 'block')
            ConstraintParser._verify_block(block, bls, c)

            # read variable
            param = ConstraintParser._read_optional(c, 'variable')
            ConstraintParser._verify_placeholder_var(param, decs, c)

            # read skip flag
            skip = bool(ConstraintParser._read_optional(c, 'skip'))

            # read option
            opt = ConstraintParser._read_optional(c, 'option')
            ConstraintParser._verify_json_syntax(block, param, opt, c)
            if opt and param:
                ConstraintParser._verify_var_option(param, opt, decs, c)
            if opt and block:
                ConstraintParser._verify_block_option(block, opt, bl_decs, c)

            # read condition
            cond = ConstraintParser._read_required(c, 'condition')
            code, parsed_decs = ConditionParser(cond).parse()
            if len(parsed_decs) % 2 == 1:
                ConstraintParser._throw('Binary operator expected', c)
            ConstraintParser._verify_condition_vars(parsed_decs, decs, bls, c)

            # now transform it into valid python code
            recon = self._recon(code, parsed_decs, cond)

            # save
            key = '{}:{}'.format(param, opt) if param is not None else \
                (block if opt is None else '{}:{}'.format(block, opt))
            self.constraints[key] = Constraint(block, param, opt, skip, recon)

        return self.constraints
