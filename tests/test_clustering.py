import unittest

# setting path
from src.self_automation import SelfAutomation


# tests for clustering related functions in SelfAutomation module
class TestClustering(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

    # calculating distance between time attribute
    def test_log_dist1(self):
        func = self.automation.log_dist
        w = self.automation.weight[0]

        time1 = [('timestamp', '2022-01-01T18:00:00.000Z')]
        time2 = [('timestamp', '2022-01-01T18:10:00.000Z')]
        time3 = [('timestamp', '2022-01-01T17:30:00.000Z')]

        self.assertEqual(0, func(time1, time1))
        self.assertEqual(10 * w, func(time1, time2))
        self.assertEqual(30 * w, func(time1, time3))

        # 24:00 equals 00:00 in time domain
        func = self.automation.log_dist
        w = self.automation.weight[0]

        time1 = [('timestamp', '2022-01-01T23:55:00.000Z')]
        time2 = [('timestamp', '2022-01-01T00:00:00.000Z')]
        time3 = [('timestamp', '2022-01-01T00:05:00.000Z')]

        self.assertEqual(0, func(time1, time1))
        self.assertEqual(5 * w, func(time1, time2))
        self.assertEqual(5 * w, func(time2, time3))

    def test_log_dist2(self):
        func = self.automation.log_dist
        w = self.automation.weight[1]

        sen1 = [('timestamp', '2022-01-01T23:55:00.000Z'), ('sensor', [50])]
        sen2 = [('timestamp', '2022-01-01T23:55:00.000Z'), ('sensor', [60])]
        sen3 = [('timestamp', '2022-01-01T23:55:00.000Z'), ('sensor', [40])]

        self.assertEqual(0, func(sen1, sen1))
        self.assertEqual(10 * w, func(sen1, sen2))
        self.assertEqual(20 * w, func(sen2, sen3))

    def test_log_dis3(self):
        func = self.automation.log_dist
        w = self.automation.weight[2]

        sen1 = [('timestamp', '2022-01-01T23:55:00.000Z'), ('sensor', ['active'])]
        sen2 = [('timestamp', '2022-01-01T23:55:00.000Z'), ('sensor', ['inactive'])]

        self.assertEqual(0, func(sen1, sen1))
        self.assertEqual(1 * w, func(sen1, sen2))

        func = self.automation.log_dist
        w0 = self.automation.weight[0]
        w1 = self.automation.weight[1]
        w2 = self.automation.weight[2]

        sen1 = [('timestamp', '2022-01-01T23:55:00.000Z'), ('sensor', ['active', 50]), ('switch', ['on'])]
        sen2 = [('timestamp', '2022-01-01T23:55:00.000Z'), ('sensor', ['inactive', 60]), ('switch', ['on'])]
        sen3 = [('timestamp', '2022-01-01T23:50:00.000Z'), ('sensor', ['inactive', 60]), ('switch', ['off'])]

        self.assertEqual(0, func(sen1, sen1))
        self.assertEqual(1 * w2 + 10 * w1, func(sen1, sen2))
        self.assertEqual(5 * w0 + 1 * w2 + 10 * w1 + 1 * w2, func(sen1, sen3))

    # find representative value of time attribute
    def test_avg_time(self):
        rep, var, _ = SelfAutomation.avg_time(
            ['2022-01-01T18:00:00.000Z', '2022-01-01T18:00:00.000Z', '2022-01-01T18:00:00.000Z'])
        self.assertEqual('18:00', rep)
        self.assertEqual(0, round(var, 3))

        rep, var, _ = SelfAutomation.avg_time(
            ['2022-01-01T12:00:00.000Z', '2022-01-01T00:00:00.000Z'])
        self.assertEqual('06:00', rep)
        self.assertEqual(1, round(var, 3))

        # 00:00 case
        rep, var, _ = SelfAutomation.avg_time(
            ['2022-01-01T23:55:00.000Z', '2022-01-01T00:00:00.000Z', '2022-01-01T00:05:00.000Z'])
        self.assertEqual('00:00', rep)

        # small variance
        rep, var, _ = SelfAutomation.avg_time(
            ['2022-01-01T17:50:00.000Z', '2022-01-01T17:55:00.000Z', '2022-01-01T18:00:00.000Z',
             '2022-01-01T18:05:00.000Z', '2022-01-01T18:10:00.000Z'])
        self.assertEqual('18:00', rep)
        self.assertGreater(0.2, var)

        # large variance
        rep, var, _ = SelfAutomation.avg_time(
            ['2022-01-01T14:00:00.000Z', '2022-01-01T16:00:00.000Z', '2022-01-01T18:00:00.000Z',
             '2022-01-01T20:00:00.000Z', '2022-01-01T22:00:00.000Z'])
        self.assertEqual('18:00', rep)
        self.assertLess(0.2, var)

        # return min and max value
        rep, var, end = SelfAutomation.avg_time(
            ['2022-01-01T17:50:00.000Z', '2022-01-01T17:55:00.000Z', '2022-01-01T18:00:00.000Z',
             '2022-01-01T18:05:00.000Z', '2022-01-01T18:10:00.000Z'])
        self.assertEqual('18:00', rep)
        self.assertEqual('17:50', end[0])
        self.assertEqual('18:10', end[1])

    def test_avg_int(self):
        rep, var, _ = SelfAutomation.avg_int([10, 10, 10])
        self.assertEqual(10, rep)
        self.assertEqual(0, var)

        # large variance
        rep, var, _ = SelfAutomation.avg_int([10, 10, 100, 0])
        self.assertEqual(30, rep)
        self.assertEqual(1650, var)

        # small variance
        rep, var, _ = SelfAutomation.avg_int([55, 60, 60, 65])
        self.assertEqual(60, rep)
        self.assertEqual(12.5, var)

        # return median as 3rd value
        rep, var, med = SelfAutomation.avg_int([25, 30, 36])
        self.assertEqual(med, 30)
        self.assertGreater(rep, med)  # mean is larger than median

        rep, var, med = SelfAutomation.avg_int([24, 30, 35])
        self.assertEqual(med, 30)
        self.assertLess(rep, med)  # mean is smaller than median

    def test_avg_str(self):
        # large ratio
        rep, rat = SelfAutomation.avg_str(['active', 'active', 'active', 'active', 'inactive'])
        self.assertEqual('active', rep)
        self.assertEqual(0.8, rat)

        # small ratio
        rep, rat = SelfAutomation.avg_str(['active', 'active', 'active', 'inactive', 'inactive'])
        self.assertEqual('active', rep)
        self.assertEqual(0.6, rat)

    # find representative
    def test_find_point(self):
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z'), ('sensor', [55]), ('switch', ['active'])],
                [('timestamp', '2022-01-01T17:55:00.000Z'), ('sensor', [60]), ('switch', ['active'])],
                [('timestamp', '2022-01-01T18:00:00.000Z'), ('sensor', [60]), ('switch', ['active'])],
                [('timestamp', '2022-01-01T18:00:00.000Z'), ('sensor', [60]), ('switch', ['active'])],
                [('timestamp', '2022-01-01T18:05:00.000Z'), ('sensor', [65]), ('switch', ['inactive'])]]
        point = [('time', ('18:00', ('17:55', '18:05'))), ('sensor:0', (60, 60)), ('switch:0', 'active')]

        self.assertEqual(point, self.automation.find_point(logs))

        # some values are rejected if variance is too high or ratio is too low
        logs = [[('timestamp', '2022-01-01T12:00:00.000Z'), ('sensor', [55]), ('switch', ['active'])],
                [('timestamp', '2022-01-01T17:55:00.000Z'), ('sensor', [60]), ('switch', ['active'])],
                [('timestamp', '2022-01-01T18:00:00.000Z'), ('sensor', [10]), ('switch', ['active'])],
                [('timestamp', '2022-01-01T12:00:00.000Z'), ('sensor', [10]), ('switch', ['inactive'])],
                [('timestamp', '2022-01-01T18:05:00.000Z'), ('sensor', [65]), ('switch', ['inactive'])]]
        point = []

        self.assertEqual(point, self.automation.find_point(logs))

    # test whether cluster_log() functions w/o error
    def test_cluster_log(self):
        logs = [[('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')], [('timestamp', '2022-01-01T18:00:00.000Z')],
                [('timestamp', '2022-01-01T18:00:00.000Z')]]

        ret = self.automation.cluster_log(logs)

        self.assertEqual(1, len(ret))
        self.assertEqual([("time", ('18:00', ('18:00', '18:00')))], ret[0])
