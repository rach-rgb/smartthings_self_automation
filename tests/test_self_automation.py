import unittest

# setting path
from src.self_automation import SelfAutomation


class TestSelfAutomation(unittest.TestCase):
    # read_log
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




