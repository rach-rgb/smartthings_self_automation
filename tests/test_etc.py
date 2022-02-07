import unittest

from src.self_automation import SelfAutomation


class TestSelfAutomation(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

    def test_read_log(self):
        info = SelfAutomation.read_log("./logs/time.json")

        self.assertEqual("my-device", info['device'])
        self.assertEqual("on", info['history'][0]['command'])
        self.assertEqual(0, len(info['neighbors']))

    # read_log() with wrong file name
    def test_read_log2(self):
        info = SelfAutomation.read_log("./logs/invalid_file_name.json")

        self.assertIsNone(info)

    def test_cls_log(self):
        logs = [{"time": "12:00", "command": "on"}, {"time": "12:00", "command": "on"},
                    {"time": "12:00", "command": "on"}, {"time": "12:00", "command": "off"},
                    {"time": "12:00", "command": "off"}, {"time": "12:00", "command": "off"}]

        ret = SelfAutomation.cls_log(logs)

        self.assertEqual(2, len(ret))
        self.assertEqual([[('time', '12:00')], [('time', '12:00')], [('time', '12:00')]], ret['on'])
        self.assertEqual([[('time', '12:00')], [('time', '12:00')], [('time', '12:00')]], ret['off'])

        # when value is a list
        logs = [{"time": "12:00", "my-sensor": [70], "command": "on"},
                    {"time": "12:00", "my-sensor": [70, 50], "command": "off"},
                    {"time": "12:00", "my-sensor": ['active'], "command": "off2"}]

        ret = SelfAutomation.cls_log(logs)
        
        self.assertEqual([("time", "12:00"), ("my-sensor", [70])], ret['on'][0])
        self.assertEqual([("time", "12:00"), ("my-sensor", [70, 50])], ret['off'][0])
        self.assertEqual([("time", "12:00"), ("my-sensor", ['active'])], ret['off2'][0])

    def test_logs_to_dict(self):
        logs = [[('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor', [50])],
                [('timestamp', '2022-01-01T02:00:00.000Z'), ('sensor', [50])]]
        data = {'timestamp': ['2022-01-01T01:00:00.000Z', '2022-01-01T02:00:00.000Z'],
                'sensor:0': [50, 50]}

        ret = self.automation.logs_to_dict(logs)

        self.assertEqual(ret, data)

        # when there's a single log
        logs = [[('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor', [50])]]
        data = {'timestamp': ['2022-01-01T01:00:00.000Z'], 'sensor:0': [50]}

        ret = self.automation.logs_to_dict(logs)

        self.assertEqual(ret, data)

        # when 'my-device' has two values
        logs = [[('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor', [50, 'active'])],
                [('timestamp', '2022-01-01T02:00:00.000Z'), ('sensor', [60, 'inactive'])]]
        data = {'timestamp': ['2022-01-01T01:00:00.000Z', '2022-01-01T02:00:00.000Z'],
                'sensor:0': [50, 60], 'sensor:1': ['active', 'inactive']}
        ret = self.automation.logs_to_dict(logs)
        self.assertEqual(ret, data)

    def test_dict_to_log(self):
        data = {'time': '2022-01-01T01:00:00.000Z', 'sensor:0': 50}
        log = [('time', '2022-01-01T01:00:00.000Z'), ('sensor', [50])]
        self.assertEqual(log, self.automation.dict_to_log(data))

        # when there's only time attribute in a log
        data = {'time': '2022-01-01T01:00:00.000Z'}
        log = [('time', '2022-01-01T01:00:00.000Z')]
        self.assertEqual(log, self.automation.dict_to_log(data))

        # when 'sensor' has two attributes
        data = {'sensor:0': 50, 'sensor:1': 60, 'sensor:2': 70}
        log = [('sensor', [50, 60, 70])]
        self.assertEqual(log, self.automation.dict_to_log(data))

