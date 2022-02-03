import json
import numpy as np
from datetime import datetime
from cmath import rect, phase
from collections import Counter
from math import radians, degrees
from sklearn.cluster import DBSCAN
# from scipy.stats import circmean, circvar
from astropy import units as u
from astropy.stats.circstats import circmean, circvar


# generate rule and mode from logs
class SelfAutomation:
    # set hyper parameters
    def __init__(self):
        self.eps = 0.5
        self.min_samples = 3
        self.weight = [0.01, 1, 10]  # weight for time, integer, string attributes in order
        self.thld = [10, 15, 0.8]  # threshold for time, integer, string attributes in order

    # return self-generated rules
    def generate_rule(self, file_in):
        info = self.read_log(file_in)
        log_cmd = self.split_log(info['history'])
        for cmd in log_cmd.keys():
            log_rep = self.cluster_log(log_cmd[cmd])

            # build rules from representative rules

    # read device usage log of json format
    @staticmethod
    def read_log(file_name):
        with open(file_name, "r") as f:
            info = json.load(f)

        return info

    # split usage log by command
    @staticmethod
    def split_log(history):
        log_cmd = {}
        for lg in history:
            cmd = lg['command']

            pp_lg = list(i for i in lg.items() if i[0] is not 'command')

            if cmd in log_cmd:
                log_cmd[cmd].append(pp_lg)
            else:
                log_cmd[cmd] = [pp_lg]

        return log_cmd

    # distance metric for DBSCAN
    def __dist__(self, a, b, log):
        x = log[int(a[0])]
        y = log[int(b[0])]
        return self.log_dist(x, y)

    # custom distance function
    def log_dist(self, x, y):
        dist = 0
        for i in range(0, len(x)):
            if x[i][0] is 'timestamp':
                frmt = '%H:%M'
                x_dt = x[i][1][11:16]
                y_dt = y[i][1][11:16]

                time = datetime.strptime(x_dt, frmt) - datetime.strptime(y_dt, frmt)
                if time.days < 0 or time.seconds >= 43200:
                    time = datetime.strptime(y_dt, frmt) - datetime.strptime(x_dt, frmt)

                dist = dist + time.seconds / 60 * self.weight[0]
            else:
                for k in range(0, len(x[i][1])):
                    x_val = x[i][1][k]
                    y_val = y[i][1][k]
                    if type(x_val) == int:
                        dist = dist + abs(x_val - y_val) * self.weight[1]
                    elif type(x_val) == str:
                        if x_val is not y_val:
                            dist = dist + 1 * self.weight[2]
        return dist

    # get average of time and variance
    # source: https://rosettacode.org/wiki/Averages/Mean_time_of_day#Python
    @staticmethod
    def avg_time(logs):
        def mean_angle(deg):
            return degrees(phase(sum(rect(1, radians(d)) for d in deg) / len(deg)))

        frmt = '%H:%M'
        dts = [datetime.strptime(lg[11:16], frmt) for lg in logs]
        minutes = [dt.hour * 60 + dt.minute for dt in dts]

        day = 24 * 60
        angles = np.array([m * 360. / day for m in minutes]) * u.deg

        mean_angle = circmean(angles).value
        var = circvar(angles).value

        mean_seconds = mean_angle * day / 360.
        if mean_seconds < 0:
            mean_seconds += day
        h, m = divmod(mean_seconds, 60)

        return '%02i:%02i' % (h, m), var

    # get representative of string value and ratio
    # assume two possible state
    @staticmethod
    def avg_str(logs):
        counter = Counter(logs).most_common(1)

        return counter[0][0], counter[0][1]/len(logs)

    # get representative of int value and variance
    @staticmethod
    def avg_int(logs):
        return np.mean(logs), np.var(logs)

    # find representative point of cluster
    def find_point(self, cluster):
        assert(len(cluster) > 0)
        assert(cluster[0][0][0] is 'timestamp')  # first attribute is always timestamp

        # make dataframe
        sample = cluster[0]
        data = {}
        for lg in sample:
            if type(lg[1]) is list:
                for i in range(0, len(lg[1])):
                    data[lg[0]+str(i)] = [lg[1][i]]
            else:
                data[lg[0]] = [lg[1]]

        if len(cluster) > 1:
            for log in cluster[1:]:
                for lg in log:
                    if type(lg[1]) is list:
                        for i in range(0, len(lg[1])):
                            data[lg[0] + str(i)].append(lg[1][i])
                    else:
                        data[lg[0]].append(lg[1])

        # get mean of each column

        # reject if deviation is larger than threshold

        # format result

        return data

    # pick representative logs
    def cluster_log(self, logs):
        x = np.arange(len(logs)).reshape(-1, 1)

        dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric=self.__dist__, metric_params={'log': logs}).fit(x)
        label = dbscan.labels_

        n_clusters_ = len(set(label)) - (1 if -1 in label else 0)
        cluster = {lab: [] for lab in range(n_clusters_)}
        for i in x:
            idx = int(i[0])
            if label[idx] == -1:
                continue
            cluster[label[idx]].append(logs[idx])

        ret = []
        for lab in range(n_clusters_):
            ret.append(self.find_point(cluster[lab]))

        return ret
