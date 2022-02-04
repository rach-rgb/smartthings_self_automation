import json
import numpy as np
from datetime import datetime
from collections import Counter
from sklearn.cluster import DBSCAN
from astropy import units as u
from astropy.stats.circstats import circmean, circvar


# generate rule and mode from logs
class SelfAutomation:
    # set hyper parameters
    def __init__(self, param=None):
        if param is None:
            self.eps = 0.5
            self.min_samples = 3
            self.weight = [1, 1, 1]  # weight for time, integer, string attributes in order
            self.thld = [0.001, 15, 0.8]  # threshold for time, integer, string attributes in order
        else:
            self.eps = param['eps']
            self.min_samples = param['min_samples']
            self.weight = [param['wtime'], param['wint'], param['wstr']]
            self.thld = [param['ttime'], param['tint'], param['tstr']]

    # return self-generated rules
    def generate_rule(self, file_in):
        info = self.read_log(file_in)
        log_cmd = self.cls_log(info['history'])
        for cmd in log_cmd.keys():
            log_rep = self.cluster_log(log_cmd[cmd])

            # build rules from representative rules
            # TODO

    # metric function for DBSCAN
    def __dist__(self, a, b, log):
        x = log[int(a[0])]
        y = log[int(b[0])]
        return self.log_dist(x, y)

    # return distance between two logs x and y
    def log_dist(self, x, y):
        total = 0
        for i in range(0, len(x)):
            if x[i][0] == 'timestamp':
                frmt = '%H:%M'
                x_time = x[i][1][11:16]
                y_time = y[i][1][11:16]

                time = datetime.strptime(x_time, frmt) - datetime.strptime(y_time, frmt)
                if time.days < 0 or time.seconds >= 43200:
                    time = datetime.strptime(y_time, frmt) - datetime.strptime(x_time, frmt)

                total = total + time.seconds / 60 * self.weight[0]
            else:
                for j in range(0, len(x[i][1])):
                    x_val = x[i][1][j]
                    y_val = y[i][1][j]
                    if type(x_val) == int:
                        total = total + abs(x_val - y_val) * self.weight[1]
                    elif type(x_val) == str:
                        if x_val is not y_val:
                            total = total + 1 * self.weight[2]
        return total

    # find representative point of cluster
    def find_point(self, cluster):
        assert(len(cluster) > 0)
        assert(cluster[0][0][0] is 'timestamp')  # first attribute is always timestamp

        data = self.logs_to_dict(cluster)

        # get mean of each column
        ret = {}
        for k, v in data.items():
            if k == "timestamp":
                avg, var = self.avg_time(v)
                if var <= self.thld[0]:
                    ret['time'] = avg
            elif type(v[0]) is int:
                avg, var = self.avg_int(v)
                if var <= self.thld[1]:
                    ret[k] = avg
            elif type(v[0]) is str:
                avg, rat = self.avg_str(v)
                if rat >= self.thld[2]:
                    ret[k] = avg

        return self.dict_to_log(ret)

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

    # static methods
    # return a usage log as a dictionary
    @staticmethod
    def read_log(file_name):
        try:
            with open(file_name, "r") as f:
                info = json.load(f)
            return info
        except FileNotFoundError as e:
            print(e)
            return None

    # return a dictionary of logs,
    # using 'command' as a key and a list of corresponding logs as a value
    @staticmethod
    def cls_log(logs):
        log_dict = {}
        for lg in logs:
            cmd = lg['command']

            # exclude value of 'command' from list
            lg_list = list(i for i in lg.items() if i[0] is not 'command')

            if cmd in log_dict:
                log_dict[cmd].append(lg_list)
            else:
                log_dict[cmd] = [lg_list]

        return log_dict

    # return a dictionary using a name of an attribute as a key and
    # a list of corresponding values as a value
    @staticmethod
    def logs_to_dict(logs):
        ret = {}
        for lg in logs[0]:
            if type(lg[1]) is list:  # split the list and name each attribute as 'device-name' + count
                for i in range(0, len(lg[1])):
                    ret[lg[0] + ':' + str(i)] = [lg[1][i]]
            else:
                ret[lg[0]] = [lg[1]]

        if len(logs) > 1:
            for log in logs[1:]:
                for lg in log:
                    if type(lg[1]) is list:
                        for i in range(0, len(lg[1])):
                            ret[lg[0] + ':' + str(i)].append(lg[1][i])
                    else:
                        ret[lg[0]].append(lg[1])

        return ret

    # return a single log generated from a given dictionary
    @staticmethod
    def dict_to_log(data):
        ret = []

        prev = None
        prev_val = []
        for k, v in data.items():
            attr = k.split(':')
            if len(attr) > 1:  # keyword + num
                keyword = attr[0]
                if prev == keyword:
                    prev_val.append(v)
                else:  # new keyword
                    if prev is not None:
                        ret.append((prev, prev_val))
                    prev = keyword
                    prev_val = [v]
            else:  # time
                ret.append((k, v))

        if prev is not None:
            ret.append((prev, prev_val))

        return ret

    # return average and variance of time
    # modify source from: https://rosettacode.org/wiki/Averages/Mean_time_of_day#Python
    @staticmethod
    def avg_time(logs):
        frmt = '%H:%M'
        dts = [datetime.strptime(lg[11:16], frmt) for lg in logs]
        minutes = [dt.hour * 60 + dt.minute for dt in dts]

        # convert minutes to angle to calculate mean and variance
        day = 24 * 60
        angles = np.array([m * 360. / day for m in minutes]) * u.deg

        mean_angle = circmean(angles).value
        var = circvar(angles).value  # use angular variance

        mean_seconds = mean_angle * day / 360.
        if mean_seconds < 0:
            mean_seconds += day
        h, m = divmod(mean_seconds, 60)

        return '%02i:%02i' % (h, m), var

    # return mode of string type values and ratio
    # assume two possible state
    @staticmethod
    def avg_str(logs):
        counter = Counter(logs).most_common(1)

        return counter[0][0], counter[0][1] / len(logs)

    # return mean and variance of integer type values
    @staticmethod
    def avg_int(logs):
        return np.mean(logs), np.var(logs)
