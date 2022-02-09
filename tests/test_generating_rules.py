import unittest

# setting path
from src.self_automation import SelfAutomation


# tests for generate_rule in SelfAutomation module
class TestRuleGenerating(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

    def test_construct_name(self):
        # no neighbors
        in_dict = {"device": "my-device"}
        n_list = []
        name = SelfAutomation.construct_name(in_dict['device'], n_list, 'on')

        self.assertEqual("my-device-on", name)

        # multiple neighbors
        in_dict = {"device": "my-device", "neighbors": [{"device": "sensor"}, {"device": "switch"}]}
        n_list = [n['device'] for n in in_dict['neighbors']]
        name = SelfAutomation.construct_name(in_dict['device'], n_list, 'on')

        self.assertEqual("my-device-sensor-switch-on", name)

    def test_construct_result(self):
        in_dict = {"device": "my-device", "capability": "switch"}
        result = SelfAutomation.construct_result(in_dict['device'], in_dict['capability'], 'on')
        expect = [{'command': {"devices": ['my-device'], 'commands':[{'capability': 'switch', 'command': 'on'}]}}]

        self.assertEqual(expect, result)

    def test_construct_EveryAction(self):
        query = ('time', ('18:00', ('17:50', '18:10')))
        result = [{'command': {"devices": ['my-device'], 'commands':[{'capability': 'switch', 'command': 'on'}]}}]
        expect = {'every': {'specific': {'time': {'hour': '18', 'minute': '00'}}, 'actions': [{'command':
                  {'devices': ['my-device'], 'commands':[{'capability': 'switch', 'command': 'on'}]}}]}}

        self.assertEqual(expect, SelfAutomation.construct_EveryAction(query, result))

    def test_time_operation(self):
        query = ('time', ('18:00', ('17:50', '18:10')))
        expect = {'between': {'value': {'time': {'reference': 'Now'}}, 'start': {'time': {'hour': '17', 'minute': '50'}}
                    , 'end': {'time': {'hour': '18', 'minute': '10'}}}}

        self.assertEqual(expect, SelfAutomation.time_operation(query))

    def test_integer_operation(self):
        # when mean < median
        query = ('my-sensor', (30, 40))
        attr = 'temperature'
        expect = {"greater_than": {"left": {"device": {"devices": ["my-sensor"], "attribute": "temperature"}}, "right":
                    {"integer": 30}}}

        self.assertEqual(expect, SelfAutomation.integer_operation(query, attr))

        # when mean > median
        query = ('my-sensor', (30, 20))
        attr = 'temperature'
        expect = {"less_than": {"left": {"device": {"devices": ["my-sensor"], "attribute": "temperature"}}, "right":
            {"integer": 30}}}

        self.assertEqual(expect, SelfAutomation.integer_operation(query, attr))

    def test_string_operation(self):
        query = ('my-sensor', 'active')
        attr = 'motion'
        expect = {"equals": {"left": {"device": {"devices": ["my-sensor"], "attribute": "motion"}}, "right":
                    {"string": 'active'}}}

        self.assertEqual(expect, SelfAutomation.string_operation(query, attr))

        # remove number
        query = ('my-sensor:0', 'active')
        attr = 'motion'
        expect = {"equals": {"left": {"device": {"devices": ["my-sensor"], "attribute": "motion"}}, "right":
                    {"string": 'active'}}}

        self.assertEqual(expect, SelfAutomation.string_operation(query, attr))

    def test_construct_IfAction(self):
        # only one query
        queries = [('my-sensor:0', 'active')]
        devices = {'my-sensor': {'device': 'my-sensor', 'value': [{"attribute": 'motion'}]}}
        result = ['results']
        expect = {'if': {"equals": {"left": {"device": {"devices": ["my-sensor"], "attribute": "motion"}}, "right":
                    {"string": 'active'}}, 'then': ['results']}}

        self.assertEqual(expect, self.automation.construct_IfAction(queries, devices, result))

        # several queries
        queries = [('my-sensor:0', 'active'), ('my-sensor:1', (50, 20)), ('my-device:0', 'active'),
                   ('time', ('18:00', ('17:50', '18:10')))]
        devices = {'my-sensor': {'device': 'my-sensor', 'value': [{"attribute": 'motion'}, {'attribute': 'temp'}]},
                   'my-device': {'device': 'my-device', 'value': [{"attribute": 'motion2'}]}}
        result = ['results']
        expect = {'if': {'and': [{"equals": {"left": {"device": {"devices": ["my-sensor"], "attribute": "motion"}},
                                            "right": {"string": 'active'}}},
                {"less_than": {"left": {"device": {"devices": ["my-sensor"], "attribute": "temp"}},
                            "right": {"integer": 50}}},
                {"equals": {"left": {"device": {"devices": ["my-device"], "attribute": "motion2"}},
                            "right": {"string": 'active'}}},
                {'between': {'value': {'time': {'reference': 'Now'}},
                'start': {'time': {'hour': '17', 'minute': '50'}}, 'end': {'time': {'hour': '18', 'minute': '10'}}}}],
                         'then': result}}

        self.assertEqual(expect, self.automation.construct_IfAction(queries, devices, result))

    def test_generate_rule(self):
        info = {'device': 'my-dev', 'capability': 'switch', 'neighbors': [{'device': 'my-sensor', 'value': [
            {"attribute": 'motion'}, {'attribute': 'status'}]}]}
        log = [('my-sensor:0', 'active'), ('my-sensor:1', (50, 20))]
        cmd = 'on'

        # expected result
        op1 = {'equals': {'left': {'device': {'devices': ['my-sensor'], 'attribute': 'motion'}},
                          'right': {'string': 'active'}}}
        op2 = {'less_than': {"left": {"device": {"devices": ["my-sensor"], "attribute": "status"}},
                             "right": {"integer": 50}}}
        result = [{'command': {'devices': ['my-dev'],
                                        'commands': [{'capability': 'switch', 'command': 'on'}]}}]
        rule = {'name': 'my-dev-my-sensor-on', 'actions': [{'if': {'and': [op1, op2], 'then': result}}]}

        self.assertEqual(rule, self.automation.generate_rule(info, log, cmd))

        # build EveryAction if there's only time condition
        log = [('time', ('18:00', ('17:50', '18:10')))]

        # expected result
        op = {'every': {'specific': {'time': {'hour': '18', 'minute': '00'}}, 'actions': result}}
        rule = {'name': 'my-dev-my-sensor-on', 'actions': [op]}

        self.assertEqual(rule, self.automation.generate_rule(info, log, cmd))
