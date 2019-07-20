#!/usr/bin/env python3

from dataclasses import dataclass
import re

# valid id pattern
pattern = '^[a-zA-Z][a-zA-Z0-9_]*'
pattern_full = '\'{{' + pattern[1:] + '}}\''


@dataclass
class Decision:
    var: str
    type: str
    value: list
    desc: str = ''


class InvalidSyntaxError(SyntaxError):
    pass


class DecisionParser:
    def __init__(self, spec):
        self.spec = spec
        self.decisions = {}

    @staticmethod
    def _is_id(s):
        return re.match(pattern, s)

    @staticmethod
    def _is_type(s):
        return s == 'discrete'

    @staticmethod
    def _read_value(s):
        try:
            res = list(s)
        except ValueError:
            raise InvalidSyntaxError('Cannot handle value "{}"'.format(s))
        return res

    def _read_json_safe(self, obj, field):
        if field not in obj:
            raise InvalidSyntaxError('Cannot find "{}" in json'.format(field))
        return obj[field]

    def _check_type(self, var, fun, msg):
        if not fun(var):
            raise InvalidSyntaxError('Cannot handle {} "{}"'.format(msg, var))
        return var

    def read_decisions(self):
        """
        Read decisions from the JSON spec.
        :return: a dict of decisions
        """
        res = {}

        for d in self._read_json_safe(self.spec, 'decisions'):
            desc = d['desc'] if 'desc' in d else 'Decision {}'.format(d['var'])

            var = self._check_type(self._read_json_safe(d, 'var'),
                                   DecisionParser._is_id, 'id')
            tp = self._check_type(self._read_json_safe(d, 'type'),
                                  DecisionParser._is_type, 'type')
            value = self._read_value(self._read_json_safe(d, 'value'))

            decision = Decision(var, tp, value, desc)
            res[var] = decision

        self.decisions = res
        return res

    def get_num_alt(self, dec):
        """
        Return the number of possible alternatives.
        For discrete type, it's the number of values.
        :param dec: variable ID of a decision
        :return: number
        """
        return len(self.decisions[dec].value)

    def gen_code(self, template, dec_id, i_alt):
        """
        Replace the placeholder variable in a template chunk.
        :param template: a chunk of code with only one placeholder
        :param dec_id: variable ID of the decision
        :param i_alt: which alternative
        :return: string - replaced code
        """
        dec = self.decisions[dec_id]
        v = dec.value[i_alt]

        # assuming the placeholder var is always at the end
        # which is true given how we chop up the chunks
        return re.sub(pattern_full + '$', str(v), template)

    def parse_code(self, line):
        """
        Find placeholder variables in a line of code.
        :param line: a line of code
        :return: (variables, chunks) a list of found variables and a list of
                 code chunks, each containing one variable
        """
        code = []
        res = []
        i = 0

        for m in re.finditer(pattern_full, line):
            val = m.group().strip('{}\'')
            if val not in set(self.decisions.keys()):
                msg = 'Cannot find the matching variable "{}" in spec'.format(val)
                raise InvalidSyntaxError(msg)
            code.append(line[i:m.end()])
            res.append(val)
            i = m.end()

        code.append(line[i:])
        return res, code
