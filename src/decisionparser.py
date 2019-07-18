#!/usr/bin/env python3

from dataclasses import dataclass
import re

# valid id pattern
pattern = '^[a-zA-Z][a-zA-Z0-9_]*'


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
        self.ids = set()

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

        self.ids = set(res.keys())
        return res

    def parse_code(self, line):
        res = []

        pt = '{{' + pattern[1:] + '}}'
        matches = re.findall(pt, line)

        for m in matches:
            m = m.strip('{}')
            if m not in self.ids:
                msg = 'Cannot find the matching variable "{}" in spec'.format(m)
                raise InvalidSyntaxError(msg)
            res.append(m)

        return res
