# -*- coding: utf-8 -*-

from dataclasses import dataclass
from .baseparser import ParseError, BaseParser


@dataclass
class Decision:
    var: str
    type: str
    value: list
    desc: str = ''


class DecisionParser(BaseParser):
    def __init__(self, spec):
        super(DecisionParser, self).__init__('')
        self.spec = spec
        self.decisions = {}

    @staticmethod
    def _is_syntax_start(ch):
        return ch == '{'

    @staticmethod
    def _is_id_token(s):
        if not BaseParser._is_id_start(s[0]):
            return False

        for ch in s:
            if not BaseParser._is_id(ch):
                return False

        return True

    @staticmethod
    def _is_type(s):
        return s == 'discrete'

    @staticmethod
    def _read_value(s):
        try:
            res = list(s)
        except ValueError:
            raise ParseError('Cannot handle value "{}"'.format(s))

        if len(s) == 0:
            raise ParseError('Cannot handle decision value "[]"')
        return res

    def _read_json_safe(self, obj, field):
        if field not in obj:
            raise ParseError('Cannot find "{}" in json'.format(field))
        return obj[field]

    def _check_type(self, var, fun, msg):
        if not fun(var):
            raise ParseError('Cannot handle {} "{}"'.format(msg, var))
        return var

    def read_decisions(self):
        """
        Read decisions from the JSON spec.
        :return: a dict of decisions
        """
        res = {}

        dec_spec = self.spec['decisions'] if 'decisions' in self.spec else []
        for d in dec_spec:
            desc = d['desc'] if 'desc' in d else 'Decision {}'.format(d['var'])

            var = self._check_type(self._read_json_safe(d, 'var'),
                                   DecisionParser._is_id_token, 'id')
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

    def get_cross_prod(self):
        """
        Get the maximum possible cardinality of options, computed as a cross
        product of all decisions.
        :return: number
        """
        ret = 1
        for dec in self.decisions:
            ret *= self.get_num_alt(dec)
        return ret

    def get_decs(self):
        """Get a list of decision names."""
        return [i for i in self.decisions.keys()]

    def gen_code(self, template, dec_id, i_alt):
        """
        Replace the placeholder variable in a template chunk.
        :param template: a chunk of code with only one placeholder
        :param dec_id: variable ID of the decision
        :param i_alt: which alternative
        :return: {string, string} replaced code and the value at this parameter
        """
        dec = self.decisions[dec_id]
        v = dec.value[i_alt]

        # assuming the placeholder var is always at the end
        # which is true given how we chop up the chunks
        length = 4 + len(dec_id)
        return template[:-length] + str(v), str(v)

    def parse_code(self, line):
        """
        Find placeholder variables in a line of code.
        :param line: a line of code
        :return: (variables, chunks) a list of found variables and a list of
                 code chunks, each containing one variable
        """
        code = []
        res = []
        j = 0
        self.i = 0
        self.line = line

        while not self._is_end():
            if self._is_syntax_start(self._peek_char()):
                token = self._read_while(lambda ch: ch == '{')
                if len(token) < 2:
                    continue

                if not self._is_id_start(self._peek_char()):
                    continue
                val = self._read_while(self._is_id)

                if len(val) == 0:
                    continue
                token = self._read_while(lambda ch: ch == '}', max_len=2)
                if len(token) < 2:
                    continue

                # read succeeds
                if val not in set(self.decisions.keys()):
                    msg = 'Cannot find the matching variable "{}" in spec'.format(val)
                    raise ParseError(msg)

                code.append(line[j:self.i])
                res.append(val)
                j = self.i
            else:
                self._next_char()

        code.append(line[j:])
        return res, code
