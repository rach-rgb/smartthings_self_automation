import unittest

from src.self_automation import SelfAutomation


# tests for generate_rule in SelfAutomation module
class TestClustering(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

    def test_get_dense_region(self):
        self.automation.min_sup = 3
        self.automation.time_err = 3.75
        self.automation.int_err = 5

        # process timestamp attribute
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-02T18:00:00.000Z')],
                [('timestamp', '2022-01-03T18:00:00.000Z')], [('timestamp', '2022-01-04T18:00:00.000Z')],
                [('timestamp', '2022-01-05T18:00:00.000Z')]]
        ret = self.automation.get_dense_region(logs)

        self.assertEqual([[270.0, 270.0, 270.0, 270.0, 270.0]], ret['time'])

        # remove if support < minimum support
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-02T18:00:00.000Z')],
                [('timestamp', '2022-01-03T18:00:00.000Z')], [('timestamp', '2022-01-04T18:00:00.000Z')],
                [('timestamp', '2022-01-05T18:00:00.000Z')], [('timestamp', '2022-01-06T18:00:00.000Z')],
                [('timestamp', '2022-01-07T12:00:00.000Z')], [('timestamp', '2022-01-08T12:00:00.000Z')]]
        ret = self.automation.get_dense_region(logs)

        self.assertEqual([[270.0, 270.0, 270.0, 270.0, 270.0, 270.0]], ret['time'])

        # process time feature
        logs = [[('timestamp', '2022-01-01T17:45:00.000Z')], [('timestamp', '2022-01-02T17:50:00.000Z')],
                [('timestamp', '2022-01-03T17:55:00.000Z')], [('timestamp', '2022-01-04T18:00:00.000Z')],
                [('timestamp', '2022-01-05T18:05:00.000Z')], [('timestamp', '2022-01-06T18:10:00.000Z')],
                [('timestamp', '2022-01-07T18:15:00.000Z')], [('timestamp', '2022-01-08T12:00:00.000Z')]]
        ret = self.automation.get_dense_region(logs)

        self.assertEqual([[266.25, 267.5, 268.75, 270.0, 271.25, 272.5, 273.75]], ret['time'])

        # process numerical feature
        logs = [[('sen', 50)], [('sen', 50)], [('sen', 50)], [('sen', 28)], [('sen', 28)], [('sen', 28)], [('sen', 35)]]
        ret = self.automation.get_dense_region(logs)

        self.assertEqual([[28, 28, 28], [50, 50, 50]], ret['sen'])

        # process string feature
        logs = [[('sen', 'active')], [('sen', 'active')], [('sen', 'active')], [('sen', 'inactive')]]
        ret = self.automation.get_dense_region(logs)

        self.assertEqual(['active'], ret['sen'])

        # process multiple features
        logs = [[('sen', 'inactive'), ('dev', 50)], [('sen', 'active'), ('dev', 51)], [('sen', 'active'), ('dev', 52)],
                [('sen', 'inactive'), ('dev', 55)], [('sen', 'active'), ('dev', 20)], [('sen', 'active'), ('dev', 20)]]
        ret = self.automation.get_dense_region(logs)

        self.assertEqual(['active'], ret['sen'])
        self.assertEqual([[50, 51, 52, 55]], ret['dev'])

    def test_get_time_regions(self):
        self.automation.time_err = 3.75
        self.automation.min_sup = 2

        values = ['2022-01-01T17:45:00.000Z', '2022-01-02T17:50:00.000Z', '2022-01-03T18:00:00.000Z',
                  '2022-01-04T11:00:00.000Z', '2022-01-05T23:50:00.000Z', '2022-01-06T23:45:00.000Z']
        ret = self.automation.get_time_regions(values)

        self.assertEqual(2, len(ret))
        self.assertEqual(3, len(ret[0]))    # 17:45, 17:50, 18:00
        self.assertEqual(2, len(ret[1]))    # 23:45, 23:50

        # merge first and last interval
        values = ['2022-01-01T18:00:00.000Z', '2022-01-02T18:00:00.000Z',
                  '2022-01-01T23:50:00.000Z', '2022-01-02T00:00:00.000Z', '2022-01-03T00:10:00.000Z']
        ret = self.automation.get_time_regions(values)

        self.assertEqual(2, len(ret))
        self.assertEqual(2, len(ret[0]))    # 18:00, 18:00
        self.assertEqual(3, len(ret[1]))    # 23:50, 00:00, 00:10

        # don't merge first and last interval
        values = ['2022-01-01T00:05:00.000Z', '2022-01-02T00:10:00.000Z', '2022-01-03T00:13:00.000Z',
                  '2022-01-04T23:45:00.000Z', '2022-01-05T23:44:00.000Z', '2022-01-06T23:42:00.000Z']
        ret = self.automation.get_time_regions(values)

        self.assertEqual(2, len(ret))
        self.assertEqual(3, len(ret[0]))    # 00:05, 00:10, 00:13
        self.assertEqual(3, len(ret[1]))    # 23:45, 23:44, 23:42

    def test_get_numeric_regions(self):
        self.automation.int_err = 3
        self.automation.min_sup = 3

        values = [1, 2, 20, 21, 23, 23, 23, 26, 30, 32, 33]
        self.assertEqual([[20, 21, 23, 23, 23, 26], [30, 32, 33]], self.automation.get_numeric_regions(values))

        values = [1, 2, 32, 33]
        self.assertEqual([], self.automation.get_numeric_regions(values))

    def test_get_string_regions(self):
        self.automation.min_sup = 5

        values = ['active', 'active', 'active', 'active', 'active', 'active', 'inactive', 'inactive', 'inactive']

        self.assertEqual(['active'], self.automation.get_string_regions(values))

        # return empty list if there's no dense region
        values = ['active', 'active', 'active', 'active', 'inactive', 'inactive', 'inactive']

        self.assertEqual([], self.automation.get_string_regions(values))

        # using constant minimum support allows to return both values
        values = ['active', 'active', 'active', 'active', 'active', 'active',
                  'inactive', 'inactive', 'inactive', 'inactive', 'inactive']

        self.assertEqual(['active', 'inactive'], self.automation.get_string_regions(values))

    def test_get_candidate_cluster(self):
        func = self.automation.get_candidate_cluster

        # time attribute
        regions = {'time': [[0, 3.75], [266.25, 267.5, 268.75]]}
        self.assertEqual([('time', (0, 3.75))], func(regions, [('timestamp', '2022-01-01T00:05:00.000Z')]))
        self.assertEqual([('time', (266.25, 268.75))], func(regions, [('timestamp', '2022-01-01T17:48:00.000Z')]))

        regions = {'time': [[266.25, 267.5, 268.75], [355, 358, 0, 2]]}
        self.assertEqual([('time', (355, 2))], func(regions, [('timestamp', '2022-01-01T23:58:00.000Z')]))
        self.assertEqual([('time', (355, 2))], func(regions, [('timestamp', '2022-01-01T00:05:00.000Z')]))

        # numerical attribute
        regions = {'sen': [[1, 1, 2], [20, 23, 24], [25, 25, 28]]}
        self.assertEqual([('sen', (20, 24))], func(regions, [('sen', 21)]))
        self.assertEqual([('sen', (1, 2))], func(regions, [('sen', 1)]))
        self.assertEqual([('sen', (25, 28))], func(regions, [('sen', 25)]))
        self.assertEqual([], func(regions, [('sen', 7)]))

        # string attribute
        regions = {'dev': ['active', 'inactive'], 'sen': ['on']}
        self.assertEqual([('dev', 'active')], func(regions, [('dev', 'active'), ('sen', 'off')]))

        # no candidate cluster
        self.assertEqual([], func(regions, [('sen', 'off')]))

        # get maximal cluster
        self.assertEqual([('dev', 'active'), ('sen', 'on')], func(regions, [('dev', 'active'), ('sen', 'on')]))

    # test basic utility of cluster_log with string attribute
    def test_cluster_log_str(self):
        self.automation.min_sup = 3

        # string attribute
        logs = [[('dev', 'active')], [('dev', 'active')], [('dev', 'active')], [('dev', 'active')], [('dev', 'active')],
                [('dev', 'inactive')], [('dev', 'inactive')], [('dev', 'inactive')]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('dev', 'active'), ), (('dev', 'inactive'), )], ret)

        # there's no cluster
        logs = [[('dev', 'active')], [('dev', 'active')], [('dev', 'inactive')], [('dev', 'inactive')]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([], ret)

        # cluster for multiple attributes
        logs = [[('dev', 'active'), ('sen', 'inactive')], [('dev', 'active'), ('sen', 'inactive')],
                [('dev', 'active'), ('sen', 'inactive')], [('dev', 'active'), ('sen', 'inactive')],
                [('dev', 'active'), ('sen', 'inactive')], [('dev', 'inactive'), ('sen', 'inactive')],
                [('dev', 'inactive'), ('sen', 'inactive')], [('dev', 'inactive'), ('sen', 'inactive')]]
        ret = self.automation.cluster_log(logs)

        # returns two cluster
        self.assertEqual([(('dev', 'active'), ('sen', 'inactive')), (('dev', 'inactive'), ('sen', 'inactive'))], ret)

        # cluster for multiple attributes, when every value of second attribute has small support
        logs = [[('dev', 'active'), ('sen', 'v1')], [('dev', 'active'), ('sen', 'v2')],
                [('dev', 'active'), ('sen', 'v3')], [('dev', 'active'), ('sen', 'v4')],
                [('dev', 'active'), ('sen', 'v5')]]
        ret = self.automation.cluster_log(logs)

        # returns two cluster with first attribute
        self.assertEqual([(('dev', 'active'), )], ret)

    def test_cluster_log_int(self):
        self.automation.int_err = 3
        self.automation.min_sup = 3

        # integer attribute
        logs = [[('dev', 50)], [('dev', 50)], [('dev', 50)]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('dev', 50), )], ret)

        # no cluster
        logs = [[('dev', 50)], [('dev', 50)]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([], ret)

        # report most frequent value
        logs = [[('dev', 48)], [('dev', 50)], [('dev', 50)], [('dev', 50)], [('dev', 50)], [('dev', 51)]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('dev', 50), )], ret)

        # breaking tie
        logs = [[('dev', 48)], [('dev', 48)], [('dev', 49)], [('dev', 49)], [('dev', 50)], [('dev', 51)]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('dev', 49), )], ret)

    def test_cluster_log_time(self):
        self.automation.min_sup = 3
        self.automation.time_err = 3.75

        # time attribute
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-02T18:00:00.000Z')],
                [('timestamp', '2022-01-03T18:00:00.000Z')], [('timestamp', '2022-01-04T18:00:00.000Z')],
                [('timestamp', '2022-01-05T18:00:00.000Z')], [('timestamp', '2022-01-06T18:00:00.000Z')],
                [('timestamp', '2022-01-07T12:00:00.000Z')], [('timestamp', '2022-01-08T12:00:00.000Z')]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('time', '18:00'), )], ret)

        # process 24:00 = 00:00 case
        logs = [[('timestamp', '2022-01-01T23:59:00.000Z')], [('timestamp', '2022-01-01T23:59:00.000Z')],
                [('timestamp', '2022-01-01T00:01:00.000Z')], [('timestamp', '2022-01-01T00:01:00.000Z')]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('time', '23:59'), )], ret)

        # process 24:00 = 00:00 case & breaking tie
        logs = [[('timestamp', '2022-01-01T23:55:00.000Z')], [('timestamp', '2022-01-02T23:55:00.000Z')],
                [('timestamp', '2022-01-03T00:00:00.000Z')], [('timestamp', '2022-01-01T00:00:00.000Z')],
                [('timestamp', '2022-01-05T00:05:00.000Z')], [('timestamp', '2022-01-06T00:05:00.000Z')]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('time', '00:00'), )], ret)

    def test_cluster_log_info(self):
        self.automation.min_sup = 3
        self.automation.int_err = 5
        self.automation.time_err = 3.75

        # add time interval information
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')]]
        ret = self.automation.cluster_log(logs, info=True)

        self.assertEqual([(('time', ('18:00', ('18:00', '18:00'))), )], ret)

        # add time interval information
        logs = [[('timestamp', '2022-01-01T17:50:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:10:00.000Z')]]
        ret = self.automation.cluster_log(logs, info=True)

        self.assertEqual([(('time', ('18:00', ('17:50', '18:10'))), )], ret)

        # add integer median value
        logs = [[('sen', 25)], [('sen', 30)], [('sen', 30)], [('sen', 30)], [('sen', 34)]]
        ret = self.automation.cluster_log(logs, info=True)

        self.assertEqual([(('sen', (30, 29.8)), )], ret)

        # add integer median value
        logs = [[('sen', 26)], [('sen', 30)], [('sen', 30)], [('sen', 30)], [('sen', 35)]]
        ret = self.automation.cluster_log(logs, info=True)

        self.assertEqual([(('sen', (30, 30.2)), )], ret)

        # no additional information for string value
        logs = [[('sen', 'act')], [('sen', 'act')], [('sen', 'act')]]
        ret = self.automation.cluster_log(logs, info=True)

        self.assertEqual([(('sen', 'act'), )], ret)

