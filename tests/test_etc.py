import unittest

# setting path
from src.self_automation import SelfAutomation


class TestSelfAutomation(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

    # read json log with proper format
    def test_read_log(self):
        info = SelfAutomation.read_log("./logs/time.json")

        self.assertEqual("my-device", info['device'])
        self.assertEqual("on", info['history'][0]['command'])
        self.assertEqual(0, len(info['neighbors']))

    # call read_log() with wrong file name
    def test_read_log(self):
        info = SelfAutomation.read_log("./logs/time.json")

        self.assertEqual("my-device", info['device'])
        self.assertEqual("on", info['history'][0]['command'])
        self.assertEqual(0, len(info['neighbors']))

    # split_log
    def test_split_log(self):
        log_hist = [{"time": "12:00", "command": "on"}, {"time": "12:00", "command": "on"},
                    {"time": "12:00", "command": "on"}, {"time": "12:00", "command": "off"},
                    {"time": "12:00", "command": "off"}, {"time": "12:00", "command": "off"}]

        pp = SelfAutomation.split_log(log_hist)
        self.assertEqual(2, len(pp))
        self.assertEqual(3, len(pp['on']))
        self.assertEqual(3, len(pp['off']))
        self.assertTrue(1, len(pp['on'][0]))

    # split_log when device can hold multiple values
    def test_split_log2(self):
        log_hist = [{"time": "12:00", "my-sensor": [70], "command": "on"},
                    {"time": "12:00", "my-sensor": [70, 50], "command": "off"},
                    {"time": "12:00", "my-sensor": ['active'], "command": "off2"}]

        pp = SelfAutomation.split_log(log_hist)
        self.assertEqual([("time", "12:00"), ("my-sensor", [70])], pp['on'][0])
        self.assertEqual([("time", "12:00"), ("my-sensor", [70, 50])], pp['off'][0])
        self.assertEqual([("time", "12:00"), ("my-sensor", ['active'])], pp['off2'][0])

    # make dictionary
    def test_make_dict(self):
        logs = [[('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor', [50])],
                [('timestamp', '2022-01-01T02:00:00.000Z'), ('sensor', [50])]]
        data = {'timestamp': ['2022-01-01T01:00:00.000Z', '2022-01-01T02:00:00.000Z'],
                'sensor:0': [50, 50]}
        ret = self.automation.make_dict(logs)
        self.assertEqual(ret, data)

        # edge case: when there's only one point in cluster
        logs = [[('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor', [50])]]
        data = {'timestamp': ['2022-01-01T01:00:00.000Z'],
                'sensor:0': [50]}
        ret = self.automation.make_dict(logs)
        self.assertEqual(ret, data)

        # when 'sensor' has two values
        logs = [[('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor', [50, 'active'])],
                [('timestamp', '2022-01-01T02:00:00.000Z'), ('sensor', [60, 'inactive'])]]
        data = {'timestamp': ['2022-01-01T01:00:00.000Z', '2022-01-01T02:00:00.000Z'],
                'sensor:0': [50, 60], 'sensor:1': ['active', 'inactive']}
        ret = self.automation.make_dict(logs)
        self.assertEqual(ret, data)

    # merge dictionary
    def test_format_log(self):
        log = [('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor:0', 50)]
        log_formatted = [('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor', [50])]
        self.assertEqual(log_formatted, self.automation.format_log(log))

        # when there's only timestamp in a log
        log = [('timestamp', '2022-01-01T01:00:00.000Z')]
        log_formatted = [('timestamp', '2022-01-01T01:00:00.000Z')]
        self.assertEqual(log_formatted, self.automation.format_log(log))

        # 'sensor' has two attributes
        log = [('sensor:0', 50), ('sensor:1', 60), ('sensor:2', 70)]
        log_formatted = [('sensor', [50, 60, 70])]
        self.assertEqual(log_formatted, self.automation.format_log(log))