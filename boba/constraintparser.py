# -*- coding: utf-8 -*-

import json
from dataclasses import dataclass
from .baseparser import ParseError
from .conditionparser import ConditionParser


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

    def _recon(self, code, parsed_decs, cond):
        """ Transform parsed code and decisions into valid python code """
        exe = []
        for i, d in enumerate(parsed_decs):
            if d.type == 'index_var':
                exe.append(self.make_index_var(d.value))
            elif d.type == 'var' and i % 2 == 1:
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
            if block is not None and block not in bls:
                msg = 'Block "{}" does not match any existing block ID'
                ConstraintParser._throw(msg.format(block), c)

            # read variable
            param = ConstraintParser._read_optional(c, 'variable')
            if param is not None:
                if param not in decs:
                    msg = 'Variable "{}" does not match any existing variable'
                    ConstraintParser._throw(msg.format(param), c)
                if block is not None:
                    msg = 'Cannot handle variable and block at the same line.'
                    ConstraintParser._throw(msg, c)

            # read skip flag
            skip = bool(ConstraintParser._read_optional(c, 'skip'))

            # read option
            opt = ConstraintParser._read_optional(c, 'option')
            if opt:
                if param is None and block is None:
                    msg = 'No corresponding variable/block for option "{}"'
                    ConstraintParser._throw(msg.format(opt), c)
                if param is not None:
                    opts = [str(o) for o in decs[param].value]
                    if str(opt) not in opts:
                        msg = 'Variable "{}" has no option "{}"'
                        ConstraintParser._throw(msg.format(param, opt), c)
                if block is not None and \
                        '{}:{}'.format(block, opt) not in bl_decs[block]:
                    msg = 'Block "{}" has no option "{}"'
                    ConstraintParser._throw(msg.format(block, opt), c)
            elif param is not None:
                msg = 'Must specify option for a variable.'
                ConstraintParser._throw(msg, c)

            # read condition
            cond = ConstraintParser._read_required(c, 'condition')
            code, parsed_decs = ConditionParser(cond).parse()
            # todo: ensure that the parameters and options exist

            # now transform it into valid python code
            recon = self._recon(code, parsed_decs, cond)

            # save
            key = '{}:{}'.format(param, opt) if param is not None else \
                (block if opt is None else '{}:{}'.format(block, opt))
            self.constraints[key] = Constraint(block, param, opt, skip, recon)

        return self.constraints
