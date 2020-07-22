#!/usr/bin/env python3

# Ugly hack to allow import from the root folder
import sys
import os
sys.path.insert(0, os.path.abspath('..'))

import unittest
import json
from boba.decisionparser import DecisionParser, ParseError, DiscretizationError


def abs_path(rel_path):
    return os.path.join(os.path.dirname(__file__), rel_path)


class TestDecisionParser(unittest.TestCase):

    def test_id_syntax(self):
        # valid identifiers
        self.assertTrue(DecisionParser._is_id_token('my_var'))
        self.assertTrue(DecisionParser._is_id_token('A1'))
        self.assertTrue(DecisionParser._is_id_token('a1b'))

        # invalid identifiers
        self.assertFalse(DecisionParser._is_id_token('_start'))
        self.assertFalse(DecisionParser._is_id_token('1b'))
        self.assertFalse(DecisionParser._is_id_token(' A'))

    def test_read_json(self):
        with open(abs_path('./specs/spec-good.json'), 'rb') as f:
            spec = json.load(f)
        dp = DecisionParser()
        dp.read_decisions(spec)
        ds = dp.discrete_decisions
        self.assertListEqual(list(ds.keys()), ['a', 'b'])
        self.assertEqual(ds['a'].desc, 'outlier')
        self.assertEqual(ds['b'].desc, 'Decision b')

    def test_parse_variable_def(self):
        # numbers
        dp = DecisionParser()
        line = 'a = b + {{c = 1, 2}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['c'])
        self.assertListEqual(codes, ['a = b + ', ''])
        self.assertListEqual(dp.decisions['c'].value, [1, 2])

        # strings
        line = 'family = {{fml="lognormal","normal"}}()'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['fml'])
        self.assertListEqual(codes, ['family = ', '()'])
        self.assertListEqual(dp.decisions['fml'].value, ["lognormal", "normal"])

    def test_parse_code(self):
        with open(abs_path('./specs/spec-good.json'), 'rb') as f:
            spec = json.load(f)
        dp = DecisionParser()
        dp.read_decisions(spec)

        line = ''
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        # valid pattern, no variable
        line = '{{}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        # valid pattern {{a}}
        line = "\t this is {{a}} v{{a}}riable"
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'a'])
        self.assertListEqual(codes, ['\t this is ', ' v', 'riable'])

        # invalid id start {{_a}}
        line = '{{_a}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])

        # valid pattern, back to back
        line = '{{a}}{{b}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'b'])
        self.assertListEqual(codes, ['', '', ''])

        # back to back, too few separators
        line = '{{a}}{a}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a'])
        self.assertListEqual(codes, ['', '{a}}'])

        # back to back, extra separators
        line = '{{a}}{{{b}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'b'])
        self.assertListEqual(codes, ['', '{', ''])

        # back to back, extra separators
        line = '{{a}}}{{b}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a', 'b'])
        self.assertListEqual(codes, ['', '}', ''])

        # broken + valid
        line = '{{a}{{a}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a'])
        self.assertListEqual(codes, ['{{a}', ''])

        # broken + valid
        line = '{{{{a}}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, ['a'])
        self.assertListEqual(codes, ['{{', ''])

        # no pattern
        line = "'In parsing file \"{}\":\n'.format(self.fn_script)"
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        # missing closing syntax
        line = '{{a}'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

        # missing closing syntax
        line = '{{a'
        vs, codes = dp.parse_code(line)
        self.assertListEqual(vs, [])
        self.assertListEqual(codes, [line])

     
    def test_continuous_err(self):
        path = './specs/continuous-err.json'
        with open(abs_path(path), 'rb') as f:
            spec = json.load(f)
        
        expected_errs = {
            "0" : ParseError,
            "1" : ParseError,
            "2" : ParseError,
            "3" : DiscretizationError,
            "4" : DiscretizationError,
            "5" : DiscretizationError,
            "6" : ValueError,
            "7" : ValueError,
            "8" : ValueError,
            "9" : ValueError,
            "10" : ValueError,
            "11" : ValueError,
            "12" : ValueError,
            "13" : ValueError,
            "14" : ValueError
        }

        for name, error in expected_errs.items():
            dp = DecisionParser()
            msg = 'failed at test ' + name + ' in ' + path + ', description: ' + spec[name]['decisions'][0]['desc']
            thrown = False
            try:
                dp.read_decisions(spec[name])
            except Exception as e:
                msg += ', expected exception ' + str(error) + ' recieved ' + str(type(e))
                if not isinstance(e, error):
                    self.fail(msg)
                
                thrown = True
            
            if not thrown:
                msg += ', no exception was thrown.'
                self.fail(msg)

    def test_continuous_vars(self):
        path = './specs/continuous.json'
        with open(abs_path(path), 'rb') as f:
            spec = json.load(f)

        dp = DecisionParser()
        dp.read_decisions(spec)

        expected_values = {
            "A" : [4.222109257625241,3.789772014701512,2.102857904154225,
                   1.2945837514648169,2.5563736068430427,2.0246706872520717,
                   3.918992945173863,1.5165636303946373,2.3829847707617793,2.916910197275156],

            "B" : [0.3987817096281944, 1.1764726069313014, 32.9219123935226,0.6176463558281531,
                   1173.2570343189907, 0.0004698113365446915, 3.8755331825795074,
                   0.0024111006812721804, 0.7666639469566167, 0.23430739939420894],
            
            "C" : [-0.9193411054662913, 0.162520645387909, 3.4941384662699027,
                   -0.48183922507637644, 7.067538950240607, -7.663179355454415,
                    1.3546832488443061, -6.027671921520947, -0.26570671318718925, -1.4511213531125535],
            
            "D" : [4.222109257625241,3.789772014701512, 2.102857904154225, 1.2945837514648169, 2.5563736068430427,
                   2.0246706872520717, 3.918992945173863, 1.5165636303946373, 2.3829847707617793,2.916910197275156, 17.0],
            
            "E" : [0.3987817096281944, 1.1764726069313014, 32.9219123935226, 0.6176463558281531, 1173.2570343189907, 
                   0.0004698113365446915,3.8755331825795074, 0.0024111006812721804, 0.7666639469566167,
                   0.23430739939420894, 0.0, 1.0, 2.0],

            "F" : [-0.9193411054662913, 0.162520645387909, 3.4941384662699027,-0.48183922507637644,
                    7.067538950240607, -7.663179355454415, 1.3546832488443061, -6.027671921520947, -0.26570671318718925,
                    -1.4511213531125535, 0.0, 1.0, 2.0, 3.0, 4.0],
                    
            "G" : [4.222109257625241, 3.789772014701512, 2.102857904154225, 0.3987817096281944,
                   1.1764726069313014, 32.9219123935226, -0.9193411054662913, 0.162520645387909, 3.4941384662699027],

            "H" : [4.222109257625241, 3.789772014701512, 2.102857904154225, 1.2945837514648169,
                   10.671821220562006, 14.237168684686164, 13.81887309488307, 11.275345128697108],

            "I" : [4.222109257625241, 3.789772014701512, 2.102857904154225, -1.1, 10.671821220562006, 14.237168684686164,
                   13.81887309488307, 0.0, 1.0, 2.0, 3.1415],

            "J" : [0.162520645387909, 1.3546832488443061, 0.42367414585227364, 1.0140813138657543,
                   1.3541129259415663, 0.3987817096281944, 1.1764726069313014, 0.6176463558281531, 
                   0.0004698113365446915, 0.0024111006812721804],

            "K" : [0.8320454426412622, 1.0330381586298683, 2.011393354799426, 0.9081299035634155,
                   4.110348384693913, 0.8320454426412622, 1.0330381586298683, 2.011393354799426, 
                   0.9081299035634155, 4.110348384693913],

            "L" : [-0.18386822109325826, 0.0325041290775818, 0.6988276932539805, -0.09636784501527529, 1.4135077900481214, 
                   -0.18386822109325826, 0.0325041290775818, 0.6988276932539805, -0.09636784501527529, 1.4135077900481214]
        }

        for var, expected in expected_values.items():
            self.assertEqual(dp.discrete_decisions[var].value, expected, msg="failed on test " + var)





if __name__ == '__main__':
    unittest.main()
