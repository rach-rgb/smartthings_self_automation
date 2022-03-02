import unittest

from src.self_automation import SelfAutomation


# test helper functions of SelfAutomation
class TestSelfAutomation(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

    def test_read_log(self):
        info = SelfAutomation.read_log("./logs/time.json")

        self.assertEqual("my-device", info['device'])
        self.assertEqual("on", info['history'][0]['command'])
        self.assertEqual(0, len(info['neighbors']))

        # read_log() with wrong file name
        info = SelfAutomation.read_log("./logs/invalid_file_name.json")

        self.assertIsNone(info)

    def test_cls_log(self):
        # format time component
        logs = [{"timestamp": "2022-01-01T00:00:00.000Z", "command": "on"},
                {"timestamp": "2022-01-02T06:00:00.000Z", "command": "on"},
                {"timestamp": "2022-01-03T12:00:00.000Z", "command": "off"},
                {"timestamp": "2022-01-04T18:00:00.000Z", "command": "on"},
                {"timestamp": "2022-01-05T18:00:00.000Z", "command": "off"}]
        ret = SelfAutomation.cls_log(logs)

        self.assertEqual(2, len(ret))
        self.assertEqual([[('time', 0)], [('time', 90)], [('time', 270)]], ret['on'])
        self.assertEqual([[('time', 180)], [('time', 270)]], ret['off'])

        # when value given as a list
        logs = [{"timestamp": "2022-01-01T00:00:00.000Z", "my-sensor": [70], "command": "cmd1"},
                {"timestamp": "2022-01-02T12:00.000Z", "my-sensor": [70, 50], "command": "cmd2"},
                {"timestamp": "2022-01-03T18:00:00.000Z", "my-sensor": ['active'], "command": "cmd3"}]
        ret = SelfAutomation.cls_log(logs)
        
        self.assertEqual([("time", 0), ("my-sensor:0", 70)], ret['cmd1'][0])
        self.assertEqual([("time", 180), ("my-sensor:0", 70), ("my-sensor:1", 50)], ret['cmd2'][0])
        self.assertEqual([("time", 270), ("my-sensor:0", 'active')], ret['cmd3'][0])

    def test_logs_to_dict(self):
        logs = [[('time', 0), ('sensor', 50)], [('time', 180), ('sensor', 50)]]
        ret = self.automation.logs_to_dict(logs)

        self.assertEqual(ret, {'time': [0, 180], 'sensor': [50, 50]})

        # when there's a single log
        logs = [[('time', 180), ('sensor', 50)]]
        data = {'time': [180], 'sensor': [50]}
        ret = self.automation.logs_to_dict(logs)

        self.assertEqual(ret, data)

    def test_is_time(self):
        func = SelfAutomation.is_time

        self.assertTrue(func(('time', '18:00')))
        self.assertTrue(func(('time', 0)))
        self.assertFalse(func(('sensor', 50)))

    def test_is_numeric(self):
        func = SelfAutomation.is_numeric

        self.assertTrue(func(('sensor', 50)))
        self.assertTrue(func(('sensor', (50, 50))))
        self.assertTrue(func(('sensor', 45.0)))
        self.assertTrue(func(('sensor', 45.5)))
        self.assertFalse(func(('sensor', 'active')))
        # returns true if time point represent time as angle
        self.assertTrue((func(('time', 180))))

    def test_time_to_ang(self):
        func = self.automation.time_to_ang

        self.assertEqual(0, func('2022-01-01T00:00:00.000Z'))
        self.assertEqual(90, func('2022-01-01T06:00:00.000Z'))
        self.assertEqual(180, func('2022-01-01T12:00:00.000Z'))
        self.assertEqual(270, func('2022-01-01T18:00:00.000Z'))
        self.assertEqual(3.75, func('2022-01-01T00:15:00.000Z'))

    def test_ang_to_min(self):
        func = self.automation.ang_to_time

        self.assertEqual("00:00", func(0))
        self.assertEqual("12:00", func(180))
        self.assertEqual("00:00", func(360))
