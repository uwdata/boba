# -*- coding: utf-8 -*-

import json
import random
from dataclasses import dataclass
from .baseparser import ParseError, BaseParser


@dataclass
class Decision:
    var: str
    value: list
    desc: str = ''

class SamplingError(SyntaxError):
    pass

class DecisionParser(BaseParser):
    def __init__(self):
        super(DecisionParser, self).__init__('')
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
    def sample_options(obj, sampling_method, sample_size):
        samples = []
        sampling_methods = {
            'uniform': (['min', 'max'], random.uniform), 
            'lognormal': (['mean', 'std_dev'], random.lognormvariate), 
            'normal' : (['mean', 'std_dev'], random.normalvariate)
        }

        if not sampling_method in sampling_methods:
            raise SamplingError('the sampling method ' + sampling_method + ' is not supported.')

        param_names = sampling_methods[sampling_method][0]
        sampling_function = sampling_methods[sampling_method][1]
        param_values = []
        for param_name in param_names:
            param_values.append(float(DecisionParser._read_json_safe(obj, param_name)))

        for i in range(sample_size):
            samples.append(sampling_function(*param_values))

        return samples

    @staticmethod
    def _read_options(s):
        try:
            generated_res = []
            res = list(s)
            for val in res:
                try:
                    sampling_method = str(DecisionParser._read_json_safe(val, "sampling_method"))
                    sample_size = int(DecisionParser._read_json_safe(val, "sample_size"))
                    generated_res.extend(DecisionParser.sample_options(val, sampling_method, sample_size))
                except (ParseError, TypeError):
                    if isinstance(val, list):
                        try:
                            generated_res.append(DecisionParser._read_options(val))
                        except (ValueError, ParseError):
                            pass
                    else:
                        generated_res.append(val)

        except ValueError:
            raise ParseError('Cannot handle value "{}"'.format(s))

        if len(s) == 0:
            raise ParseError('Cannot handle decision value "[]"')
        return generated_res

    @staticmethod
    def _read_json_safe(obj, field):
        if field not in obj:
            raise ParseError('Cannot find "{}" in json'.format(field))
        return obj[field]

    def _check_type(self, var, fun, msg):
        if not fun(var):
            raise ParseError('Cannot handle {} "{}"'.format(msg, var))
        return var

    def verify_naming(self, reserved):
        """
        Verify if the decision names collide with any other variable names.
        :param reserved: A list of reserved names.
        :return:
        """
        for w in reserved:
            if w in self.decisions:
                raise ParseError('Duplicate variable/block name "{}"'.format(w))

    def read_decisions(self, spec):
        """
        Read decisions from the JSON spec.
        :return: a dict of decisions
        """
        dec_spec = spec['decisions'] if 'decisions' in spec else []
        for d in dec_spec:
            desc = d['desc'] if 'desc' in d else 'Decision {}'.format(d['var'])

            var = self._check_type(DecisionParser._read_json_safe(d, 'var'),
                                   DecisionParser._is_id_token, 'id')
            value = DecisionParser._read_options(DecisionParser._read_json_safe(d, 'options'))

            # check if two variables have the same name
            if var in self.decisions:
                raise ParseError('Duplicate variable name "{}"'.format(var))

            decision = Decision(var, value, desc)
            self.decisions[var] = decision

        return self.decisions

    def get_num_alt(self, dec):
        """
        Return the number of possible alternatives.
        For discrete type, it's the number of options.
        :param dec: variable ID of a decision
        :return: number
        """
        return len(self.decisions[dec].value)

    def get_alt(self, dec, i_alt):
        """
        Return the i-th alternative. For discrete type, it's simply the i-th
        option specified.
        :param dec: variable ID of a decision
        :param i_alt: which alternative
        :return: value of the option
        """
        return self.decisions[dec].value[i_alt]

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
        v = self.get_alt(dec_id, i_alt)

        # assuming the placeholder var is always at the end
        # which is true given how we chop up the chunks
        return template + str(v), str(v)

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
        i_start = 0
        self.i = 0
        self.line = line

        while not self._is_end():
            if self._is_syntax_start(self._peek_char()):
                token = self._read_while(lambda ch: ch == '{')
                if len(token) < 2:
                    continue
                i_start = self.i - 2

                # read variable identifier
                if not self._is_id_start(self._peek_char()):
                    continue
                val = self._read_while(self._is_id)
                if len(val) == 0:
                    continue

                # read definition, if any
                df = None
                self._read_while(self._is_whitespace)
                if not self._is_end() and self._peek_char() == '=':
                    self._next_char()
                    # problem: the variable value can't contain "}"
                    df = self._read_while(lambda ch: ch != '}')
                    self._read_while(self._is_whitespace)

                token = self._read_while(lambda ch: ch == '}', max_len=2)
                if len(token) < 2:
                    continue

                # read succeeds
                code.append(line[j:i_start])
                res.append(val)
                j = self.i

                # parse and save definition
                if df:
                    try:
                        df = json.loads('[{}]'.format(df))
                        decision = Decision(val, df, '')
                        if val in self.decisions:
                            msg = 'Duplicate variable definition "{}"'
                            raise ParseError(msg.format(val))
                        self.decisions[val] = decision
                    except ValueError:
                        msg = 'Cannot parse variable definition:\n{}'
                        raise ParseError(msg.format(df))
            else:
                self._next_char()

        code.append(line[j:])
        return res, code
