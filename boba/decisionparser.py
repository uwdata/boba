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

class DiscretizationError(SyntaxError):
    pass

class DiscretizationFn:
    def __init__(self, function, required_params, optional_params):
        self.function = function
        self.required_params = required_params
        self.optional_params = optional_params

class DecisionParser(BaseParser):
    def __init__(self):
        super(DecisionParser, self).__init__('')
        self.decisions = {}
        self.discrete_decisions = {}

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
    def check_var_types(args, types, names):
        for i in range(0, len(args)):
            if not isinstance(args[i], types[i]):
                raise ValueError(names[i] + ' must be of type ' + str(types[i]))


    @staticmethod
    def get_within_range(function, args, distribution_range, exclusive):
        """bind the output of the provided function within the provided range"""
        if distribution_range[1] <= distribution_range[0]:
            raise ValueError('max value: ' + str(distribution_range[1]) + ' is less than min value: ' + str(distribution_range[0]))
        
        val = function(*args)
        while (val < distribution_range[0] or val > distribution_range[1] or
              ((val == distribution_range[0] or val == distribution_range[1]) and exclusive)):
            val = function(*args)

        return val

    @staticmethod
    def random_uniform(minimum, maximum, args):
        """randomly sample a number from a uniform distribution"""
        exclusive = args.get('exclusive', False)
        DecisionParser.check_var_types([minimum, maximum, exclusive], 
                        [float, float, bool], 
                        ['min', 'max', 'exclusive'])

        distr_range = [minimum, maximum]
        return DecisionParser.get_within_range(random.uniform, distr_range, distr_range, exclusive)

    @staticmethod
    def rand_x_normal(function, args):
        """randomly sample a number from any type of normal distribution"""
        mean = args.get('mean', 0.0)
        std_dev = args.get('std_dev', 1.0)
        exclusive = args.get('exclusive', False)
        distribution_range = args.get('range', [])
        DecisionParser.check_var_types([mean, std_dev, exclusive, distribution_range], 
                        [float, float, bool, list], 
                        ['mean', 'std_dev', 'exclusive', 'range'])

        if len(distribution_range) == 0:
            distribution_range = None

        if distribution_range and len(distribution_range) != 2:
            raise ValueError('expected two items in range list')
        elif distribution_range and len(distribution_range) == 2:
            DecisionParser.check_var_types(distribution_range, [float, float], ['range[0]', 'range[1]'])

        if distribution_range:
            return DecisionParser.get_within_range(function, [mean, std_dev], distribution_range, exclusive)
        else:
            return function(mean, std_dev)

    @staticmethod
    def random_lognormal(args):
        """randomly sample a number from a lognormal distribution"""
        return DecisionParser.rand_x_normal(random.lognormvariate, args)

    @staticmethod
    def random_normal(args):
        """randomly sample a number from a normal distribution"""
        return DecisionParser.rand_x_normal(random.normalvariate, args)

    @staticmethod
    def discretize(obj, discretization_method, count):
        """discretizes a continuous variable into 'count' descrete options."""
        discretization_methods = {
            'uniform': DiscretizationFn(DecisionParser.random_uniform, ['min', 'max'], ['exclusive']), 
            'lognormal': DiscretizationFn(DecisionParser.random_lognormal, [], ['mean', 'std_dev', 'exclusive', 'range']), 
            'normal' : DiscretizationFn(DecisionParser.random_normal, [], ['mean', 'std_dev', 'exclusive', 'range'])
        }

        if not discretization_method in discretization_methods:
            raise SamplingError('the discretization method ' + discretization_method + ' is not supported.')

        method = discretization_methods[discretization_method]
        required_param_names = method.required_params
        param_values = []
        for param_name in required_param_names:
            try:
                param_values.append(DecisionParser._read_json_safe(obj, param_name))
            except ParseError:
                raise DiscretizationError('expected ' + param_name + ' to be defined in ' + str(obj))

        optional_param_names = method.optional_params
        optional_params = {}
        for param_name in optional_param_names:
            try:
                optional_params[param_name] = DecisionParser._read_json_safe(obj, param_name)
            except ParseError:
                continue

        param_values.append(optional_params)
        fn = method.function
        samples = []
        for i in range(count):
            samples.append(fn(*param_values))

        return samples

    @staticmethod
    def _read_discrete_options(s, allow_empty_list=False):
        """reads an option, converting all continuous values into discrete ones"""
        generated_res = []
        res = DecisionParser._read_options(s, allow_empty_list)
        for val in res:
            if isinstance(val, dict):
                try:
                    sampling_method = str(DecisionParser._read_json_safe(val, "sample"))
                    count = int(DecisionParser._read_json_safe(val, "count"))
                    try:
                        seed = int(DecisionParser._read_json_safe(val, "seed"))
                        random.seed(seed)
                    except (ParseError, TypeError):
                        pass

                    generated_res.extend(DecisionParser.discretize(val, sampling_method, count))
                except (ParseError, TypeError):
                    raise ParseError('expected "sample" and "count" to be defined as string and int respectively in object:\n' + str(s))
            elif isinstance(val, list):
                generated_res.append(DecisionParser._read_discrete_options(val, True))
            else:
                generated_res.append(val)

        return generated_res

    @staticmethod
    def _read_options(s, allow_empty_list=False):
        """reads an option"""
        try:
            res = list(s)
        except ValueError:
            raise ParseError('Cannot handle value "{}"'.format(s))

        if len(s) == 0 and not allow_empty_list:
            raise ParseError('Cannot handle decision value "[]"')
        return res
        

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
        :return:
        """
        dec_spec = spec['decisions'] if 'decisions' in spec else []
        for d in dec_spec:
            desc = d['desc'] if 'desc' in d else 'Decision {}'.format(d['var'])

            var = self._check_type(DecisionParser._read_json_safe(d, 'var'),
                                   DecisionParser._is_id_token, 'id')
            value = DecisionParser._read_options(DecisionParser._read_json_safe(d, 'options'))
            discrete_value = DecisionParser._read_discrete_options(DecisionParser._read_json_safe(d, 'options'))

            # check if two variables have the same name
            if var in self.decisions:
                raise ParseError('Duplicate variable name "{}"'.format(var))

            decision = Decision(var, value, desc)
            discrete_decision = Decision(var, discrete_value, desc)
            self.decisions[var] = decision
            self.discrete_decisions[var] = discrete_decision

    def get_num_alt_discrete(self, dec):
        """
        Return the number of possible alternatives.
        For discrete type, it's the number of options.
        :param dec: variable ID of a decision
        :return: number
        """
        return len(self.discrete_decisions[dec].value)

    def get_alt_discrete(self, dec, i_alt):
        """
        Return the i-th alternative. For discrete type, it's simply the i-th
        option specified.
        :param dec: variable ID of a decision
        :param i_alt: which alternative
        :return: value of the option
        """
        return self.discrete_decisions[dec].value[i_alt]

    def get_cross_prod_discrete(self):
        """
        Get the maximum possible cardinality of options, computed as a cross
        product of all decisions.
        :return: number
        """
        ret = 1
        for dec in self.discrete_decisions:
            ret *= self.get_num_alt_discrete(dec)
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
        v = self.get_alt_discrete(dec_id, i_alt)

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
                        self.discrete_decisions[val] = decision
                    except ValueError:
                        msg = 'Cannot parse variable definition:\n{}'
                        raise ParseError(msg.format(df))
            else:
                self._next_char()

        code.append(line[j:])
        return res, code
