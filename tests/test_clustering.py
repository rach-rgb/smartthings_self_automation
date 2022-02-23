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
        values = ['2022-01-01T23:50:00.000Z', '2022-01-02T00:00:00.000Z', '2022-01-03T00:10:00.000Z']
        ret = self.automation.get_time_regions(values)

        self.assertEqual(1, len(ret))
        self.assertEqual(3, len(ret[0]))    # 23:50, 00:00, 00:10

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

    def test_add_info(self):
        # add time interval information
        logs = [[('timestamp', '2022-01-01T17:50:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:10:00.000Z')]]
        center = (('time', 270), )
        ret = self.automation.add_info(logs, center)

        self.assertEqual((('time', ('18:00', ('17:50', '18:10'))), ), ret)

        # add median information
        logs = [[('sen', 28)], [('sen', 30)], [('sen', 35)]]
        center = (('sen', 30),)
        ret = self.automation.add_info(logs, center)

        self.assertEqual((('sen', (30, 31)),), ret)

        # no additional information
        logs = [[('sen', 'act')], [('sen', 'act')], [('sen', 'act')]]
        center = (('sen', 'act'),)
        ret = self.automation.add_info(logs, center)

        self.assertEqual((('sen', 'act'), ), ret)

    def test_get_candidate_cluster(self):
        func = self.automation.get_candidate_cluster
        regions = [('time', 180), ('sensor', 'active'), ('dev', 50)]

        self.assertEqual([('time', 180)], func(regions, [('time', 180)]))
        # no candidate cluster
        self.assertEqual([], func(regions, [('time', 0)]))
        # get maximal cluster
        log = [('time', 180), ('sensor', 'active'), ('dev', 30)]
        self.assertEqual([('time', 180), ('sensor', 'active')], func(regions, log))

    # test basic utility of cluster_log with string attribute
    def test_cluster_log_str(self):
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
        self.automation.int_err = 5

        # integer attribute
        logs = [[('dev', 50)], [('dev', 50)], [('dev', 50)]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('dev', 50), )], ret)

        # no cluster
        logs = [[('dev', 50)], [('dev', 50)]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([], ret)

        # nearby value increases point
        logs = [[('dev', 49)], [('dev', 50)], [('dev', 50)], [('dev', 51)]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('dev', 50),)], ret)

        # report most dominant value
        logs = [[('dev', 50)], [('dev', 50)], [('dev', 50)], [('dev', 50)], [('dev', 50)], [('dev', 50)]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('dev', 50), )], ret)

    def test_cluster_log_time(self):
        # time attribute
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T12:00:00.000Z')], [('timestamp', '2022-01-01T12:00:00.000Z')]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('time', '18:00'), )], ret)

        # process 24:00 = 00:00 case
        logs = [[('timestamp', '2022-01-01T23:59:00.000Z')], [('timestamp', '2022-01-01T23:59:00.000Z')],
                [('timestamp', '2022-01-01T00:01:00.000Z')], [('timestamp', '2022-01-01T00:01:00.000Z')]]
        ret = self.automation.cluster_log(logs)

        self.assertEqual([(('time', '00:00'), )], ret)

    def test_cluster_log_info(self):
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

