import unittest

# setting path
from src.self_automation import SelfAutomation


# tests for generate_rule in SelfAutomation module
class TestClustering2(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

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
        self.assertFalse(('time', 266) in ret)  # 266 corresponds to 17:45
        self.assertEqual(3, ret[('time', 268)])     # 268 corresponds to 17:50
        self.assertEqual(4, ret[('time', 270)])     # 270 corresponds to 18:00
        self.assertFalse(('time', 180) in ret)

        # process real number attribute(except time)
        logs = [[('sen', 50)], [('sen', 50)], [('sen', 50)], [('sen', 48)], [('sen', 35)]]

        ret = self.automation.get_dense_region(logs)
        self.assertEqual(3.5, ret[('sen', 50)])

        # process string attribute
        logs = [[('sen', 'active')], [('sen', 'active')], [('sen', 'active')], [('sen', 'inactive')]]

        ret = self.automation.get_dense_region(logs)
        self.assertEqual(3, ret[('sen', 'active')])

    def test_get_candidate_cluster(self):
        func = self.automation.get_candidate_cluster

        regions = [('time', 180), ('sensor', 'active'), ('dev', 50)]

        self.assertEqual([('time', 180)], func(regions, [('time', 180)]))
        # no candidate cluster
        self.assertEqual([], func(regions, [('time', 0)]))
        # get maximal cluster
        log = [('time', 180), ('sensor', 'active'), ('dev', 30)]
        self.assertEqual([('time', 180), ('sensor', 'active')], func(regions, log))

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

    def test_get_interval(self):
        func = self.automation.get_interval

        # point represents time
        # round value
        self.automation.time_err = 3.75
        self.assertEqual([('time', 176), ('time', 177), ('time', 178), ('time', 179), ('time', 180), ('time', 181),
                          ('time', 182), ('time', 183), ('time', 184), ('time', 180)],
                         func(('time', '2022-01-01T12:00:00.000Z')))

        self.automation.time_err = 2
        self.assertEqual([('time', 358), ('time', 359), ('time', 0), ('time', 1), ('time', 2), ('time', 0)],
                         func(('time', '2022-01-01T00:00:00.000Z')))
        self.assertEqual([('time', 357), ('time', 358), ('time', 359), ('time', 0), ('time', 1), ('time', 359)],
                         func(('time', '2022-01-01T23:56:00.000Z')))

        # point has integer value
        self.automation.int_err = 3
        self.assertEqual([('sensor', 47), ('sensor', 48), ('sensor', 49), ('sensor', 50), ('sensor', 51),
                          ('sensor', 52), ('sensor', 53), ('sensor', 50)], func(('sensor', 50)))

        # point has string value
        self.assertEqual([('dev', 'active'), ('dev', 'active')], func(('dev', 'active')))

    # test basic utility of cluster_log with string attribute
    def test_cluster_log_str(self):
        # string attribute
        logs = [[('dev', 'active')], [('dev', 'active')], [('dev', 'active')], [('dev', 'active')], [('dev', 'active')],
                [('dev', 'inactive')], [('dev', 'inactive')], [('dev', 'inactive')]]
        ret = self.automation.cluster_log2(logs)

        self.assertEqual([(('dev', 'active'), ), (('dev', 'inactive'), )], ret)

        # there's no cluster
        logs = [[('dev', 'active')], [('dev', 'active')], [('dev', 'inactive')], [('dev', 'inactive')]]
        ret = self.automation.cluster_log2(logs)

        self.assertEqual([], ret)

        # cluster for multiple attributes
        logs = [[('dev', 'active'), ('sen', 'inactive')], [('dev', 'active'), ('sen', 'inactive')],
                [('dev', 'active'), ('sen', 'inactive')], [('dev', 'active'), ('sen', 'inactive')],
                [('dev', 'active'), ('sen', 'inactive')], [('dev', 'inactive'), ('sen', 'inactive')],
                [('dev', 'inactive'), ('sen', 'inactive')], [('dev', 'inactive'), ('sen', 'inactive')]]
        ret = self.automation.cluster_log2(logs)

        # returns two cluster
        self.assertEqual([(('dev', 'active'), ('sen', 'inactive')), (('dev', 'inactive'), ('sen', 'inactive'))], ret)

        # cluster for multiple attributes, when every value of second attribute has small support
        logs = [[('dev', 'active'), ('sen', 'v1')], [('dev', 'active'), ('sen', 'v2')],
                [('dev', 'active'), ('sen', 'v3')], [('dev', 'active'), ('sen', 'v4')],
                [('dev', 'active'), ('sen', 'v5')]]
        ret = self.automation.cluster_log2(logs)

        # returns two cluster with first attribute
        self.assertEqual([(('dev', 'active'), )], ret)

    def test_cluster_log_int(self):
        # integer attribute
        logs = [[('dev', 50)], [('dev', 50)], [('dev', 50)]]
        ret = self.automation.cluster_log2(logs)

        self.assertEqual([(('dev', 50), )], ret)

        # no cluster
        logs = [[('dev', 50)], [('dev', 50)]]
        ret = self.automation.cluster_log2(logs)

        self.assertEqual([], ret)

        # nearby value increases point
        logs = [[('dev', 49)], [('dev', 50)], [('dev', 50)], [('dev', 51)]]
        ret = self.automation.cluster_log2(logs)

        self.assertEqual([(('dev', 50),)], ret)

        # report most dominant value
        logs = [[('dev', 50)], [('dev', 50)], [('dev', 50)], [('dev', 50)], [('dev', 50)], [('dev', 50)]]
        ret = self.automation.cluster_log2(logs)

        self.assertEqual([(('dev', 50), )], ret)

    def test_cluster_log_time(self):
        # time attribute
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T12:00:00.000Z')], [('timestamp', '2022-01-01T12:00:00.000Z')]]
        ret = self.automation.cluster_log2(logs)

        self.assertEqual([(('time', '18:00'), )], ret)
        # TODO: fix error



