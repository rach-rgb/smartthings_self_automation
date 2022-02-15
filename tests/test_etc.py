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
        
        self.assertEqual([("time", "12:00"), ("my-sensor:0", 70)], ret['on'][0])
        self.assertEqual([("time", "12:00"), ("my-sensor:0", 70), ("my-sensor:1", 50)], ret['off'][0])
        self.assertEqual([("time", "12:00"), ("my-sensor:0", 'active')], ret['off2'][0])

    def test_logs_to_dict(self):
        logs = [[('timestamp', '2022-01-01T01:00:00.000Z'), ('sensor', [50])],
                [('timestamp', '2022-01-01T02:00:00.000Z'), ('sensor', [50])]]
        data = {'timestamp': ['2022-01-01T01:00:00.000Z', '2022-01-01T02:00:00.000Z'], 'sensor:0': [50, 50]}
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

    def test_is_time(self):
        func = SelfAutomation.is_time
        self.assertTrue(func(('timestamp', '2022-01-01T01:00:00.000Z')))
        self.assertTrue(func(('time', '18:00')))
        self.assertTrue(func(('time', 0)))
        self.assertFalse(func(('sensor', 50)))

    def test_is_int(self):
        func = SelfAutomation.is_int
        self.assertTrue(func(('sensor', 50)))
        self.assertTrue(func(('sensor', (50, 50))))
        self.assertFalse(func(('sensor', 'active')))
        # returns true if time point represent time as angle
        self.assertTrue((func(('time', 180))))

    def test_ang_to_min(self):
        func = self.automation.ang_to_min

        self.assertEqual("00:00", func(0))
        self.assertEqual("12:00", func(180))
        self.assertEqual("00:00", func(360))

    def test_time_to_ang(self):
        func = self.automation.time_to_ang

        self.assertEqual(0, func('2022-01-01T00:00:00.000Z'))
        self.assertEqual(90, func('2022-01-01T06:00:00.000Z'))
        self.assertEqual(180, func('2022-01-01T12:00:00.000Z'))
        self.assertEqual(270, func('2022-01-01T18:00:00.000Z'))
        self.assertEqual(3.75, func('2022-01-01T00:15:00.000Z'))

    def test_time_info(self):
        # return min and max value
        ret = SelfAutomation.time_info(
            ['2022-01-01T17:50:00.000Z', '2022-01-01T17:55:00.000Z', '2022-01-01T18:00:00.000Z',
             '2022-01-01T18:05:00.000Z', '2022-01-01T18:10:00.000Z'])
        self.assertEqual('17:50', ret[0])
        self.assertEqual('18:10', ret[1])

        # return min and max value
        ret = SelfAutomation.time_info(
            ['2022-01-01T18:00:00.000Z', '2022-01-01T18:00:00.000Z', '2022-01-01T18:00:00.000Z',
             '2022-01-01T18:00:00.000Z', '2022-01-01T18:00:00.000Z'])
        self.assertEqual('18:00', ret[0])
        self.assertEqual('18:00', ret[1])

    def test_int_info(self):
        self.assertEqual(10, SelfAutomation.int_info([10, 10, 10]))
        self.assertEqual(10, SelfAutomation.int_info([13, 10, 7]))
