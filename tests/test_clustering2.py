import unittest

# setting path
from src.self_automation import SelfAutomation


# tests for generate_rule in SelfAutomation module
class TestRuleGenerating(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

    def test_cluster_log2(self):
        self.assertTrue(1)

    def test_get_dense_region(self):
        # process timestamp attribute
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')]]

        ret = self.automation.get_dense_region(logs)
        self.assertEqual(5, ret[('time', 270)])

        # remove if support < minsup
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T12:00:00.000Z')], [('timestamp', '2022-01-01T12:00:00.000Z')]]

        ret = self.automation.get_dense_region(logs)
        self.assertFalse(('time', 180) in ret)

        # process real number attribute(time)
        logs = [[('timestamp', '2022-01-01T17:45:00.000Z')], [('timestamp', '2022-01-01T17:50:00.000Z')],
                [('timestamp', '2022-01-01T17:55:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:05:00.000Z')], [('timestamp', '2022-01-01T18:10:00.000Z')],
                [('timestamp', '2022-01-01T18:15:00.000Z')], [('timestamp', '2022-01-01T12:00:00.000Z')]]

        ret = self.automation.get_dense_region(logs)
        self.assertEqual(4, ret[('time', 266)])
        self.assertEqual(7, ret[('time', 270)])
        self.assertFalse(('time', 180) in ret)

        # process real number attribute(except time)
        logs = [[('sen', 50)], [('sen', 50)], [('sen', 48)], [('sen', 35)]]

        ret = self.automation.get_dense_region(logs)
        self.assertEqual(3, ret[('sen', 50)])

        # process string attribute
        logs = [[('sen', 'active')], [('sen', 'active')], [('sen', 'active')], [('sen', 'inactive')]]

        ret = self.automation.get_dense_region(logs)
        self.assertEqual(3, ret[('sen', 'active')])

    def test_get_candidate_cluster(self):
        self.assertTrue(1)

    def test_time_to_ang(self):
        func = self.automation.time_to_ang

        self.assertEqual(0, func('2022-01-01T00:00:00.000Z'))
        self.assertEqual(90, func('2022-01-01T06:00:00.000Z'))
        self.assertEqual(180, func('2022-01-01T12:00:00.000Z'))
        self.assertEqual(270, func('2022-01-01T18:00:00.000Z'))
        self.assertEqual(3.75, func('2022-01-01T00:15:00.000Z'))

    def test_get_interval(self):
        func = self.automation.get_interval

        # point represents time
        # round value
        self.automation.time_err = 3.75
        self.assertEqual([('time', 176), ('time', 177), ('time', 178), ('time', 179), ('time', 180), ('time', 181),
                          ('time', 182), ('time', 183), ('time', 184)], func(('time', '2022-01-01T12:00:00.000Z')))

        self.automation.time_err = 2
        self.assertEqual([('time', 358), ('time', 359), ('time', 0), ('time', 1), ('time', 2)],
                         func(('time', '2022-01-01T00:00:00.000Z')))
        self.assertEqual([('time', 357), ('time', 358), ('time', 359), ('time', 0), ('time', 1)],
                         func(('time', '2022-01-01T23:56:00.000Z')))

        # point has integer value
        self.automation.int_err = 3
        self.assertEqual([('sensor', 47), ('sensor', 48), ('sensor', 49), ('sensor', 50), ('sensor', 51),
                          ('sensor', 52), ('sensor', 53)], func(('sensor', 50)))

        # point has string value
        self.assertEqual([('dev', 'active')], func(('dev', 'active')))
