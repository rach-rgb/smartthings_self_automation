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
    def __init__(self, input_dir='./logs/', param=None):
        self.input_dir = input_dir
        if param is None:
            self.eps = 720
            self.min_samples = 1
            self.weight = [1, 3, 180]  # weight for time, integer, string attributes in order
            self.thld = [0.001, 15, 0.8]  # threshold for time, integer, string attributes in order
        else:
            self.eps = param['eps']
            self.min_samples = param['min_samples']
            self.weight = [param['wtime'], param['wint'], param['wstr']]
            self.thld = [param['ttime'], param['tint'], param['tstr']]

        self.minsup = 3     # minimum support
        self.time_err = 3.75    # acceptable time error(15 minute) as angle
        self.int_err = 5

    # save self-generated rules at director file_out_dir
    def run(self, file_in, dir_out):
        info = self.read_log(self.input_dir + file_in)
        log_cmd = self.cls_log(info['history'])
        results = []
        for cmd in log_cmd.keys():
            logs = self.cluster_log(log_cmd[cmd])

            # build rules from representative rules
            if len(logs) == 0:
                print("No rule is detected")
            for idx, log in enumerate(logs):
                rule = self.generate_rule(info, log, cmd)

                if len(logs) == 1:
                    file_out = file_in.split('.')[0] + '_' + cmd + '_rule.json'
                else:
                    file_out = file_in.split('.')[0] + '_' + cmd + str(idx) + '_rule.json'
                results.append(file_out)

                with open(dir_out + file_out, 'w') as f:
                    json.dump(rule, f)

        return results

    # return rule built from info and logs
    def generate_rule(self, info, log, cmd):
        # create name of rule
        n_dict = {n['device']: n for n in info['neighbors']}

        name = self.construct_name(info['device'], n_dict.keys(), cmd)

        # create result part of rule
        result = self.construct_result(info['device'], info['capability'], cmd)

        # create rule
        # construct EveryAction if there's only a time query
        if len(log) == 1 and log[0][0] == 'time':
            action = self.construct_EveryAction(log[0], result)
        else:
            action = self.construct_IfAction(log, n_dict, result)

        rule = {'name': name, 'actions': [action]}

        return rule

    # return name of rule
    @staticmethod
    def construct_name(cur_device, n_devices, cmd):
        name = cur_device
        for n in n_devices:
            name = name + '-' + n
        name = name + '-' + cmd
        return name

    # return result of rule('then' part)
    @staticmethod
    def construct_result(cur_device, cap, cmd):
        action = [{'command': {"devices": [cur_device], 'commands': [{'capability': cap, 'command': cmd}]}}]
        return action

    # return condition of rule with IfAction format
    def construct_IfAction(self, queries, devices, result):
        operations = []
        for q in queries:
            if q[0] == 'time':
                operations.append(self.time_operation(q))
            else:
                info = q[0].split(':')
                name = info[0]
                num = int(info[1])
                attr = devices[name]['value'][num]['attribute']
                if type(q[1]) == str:
                    operations.append(self.string_operation(q, attr))
                else:  # integer
                    operations.append(self.integer_operation(q, attr))

        if len(operations) == 1:
            operations[0]['then'] = result
            ret = {'if': operations[0]}
        else:
            ret = {'if': {'and': []}}
            for op in operations:
                ret['if']['and'].append(op)
            ret['if']['then'] = result

        return ret

    # return condition of rule with EveryAction format
    # used for time condition
    @staticmethod
    def construct_EveryAction(time_query, result):
        hour = int(time_query[1][0][0:2])
        minute = int(time_query[1][0][3:5])

        operation = {'time': {'hour': hour, 'minute': minute}}
        return {'every': {'specific': operation, 'actions': result}}

    @staticmethod
    def time_operation(query):
        start_h = int(query[1][1][0][0:2])
        start_m = int(query[1][1][0][3:5])
        end_h = int(query[1][1][1][0:2])
        end_m = int(query[1][1][1][3:5])
        operation = {'between': {'value': {'time': {'reference': 'Now'}}, 'start': {'time': {'hour': start_h,
                                                                                             'minute': start_m}},
                                 'end': {'time': {'hour': end_h, 'minute': end_m}}}}

        return operation

    @staticmethod
    def integer_operation(query, attr):
        if query[1][0] < query[1][1]:
            op = 'greater_than'
        else:
            op = 'less_than'
        operation = {op: {"left": {"device": {"devices": [query[0].split(':')[0]], "attribute": attr}},
                          "right": {"integer": query[1][0]}}}

        return operation

    @staticmethod
    def string_operation(query, attr):
        operation = {"equals": {"left": {"device": {"devices": [query[0].split(':')[0]], "attribute": attr}},
                                "right": {"string": query[1]}}}
        return operation

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
        assert (len(cluster) > 0)
        assert (cluster[0][0][0] == 'timestamp')  # first attribute is always timestamp

        data = self.logs_to_dict(cluster)

        # get mean of each column
        ret = {}
        for k, v in data.items():
            if k == "timestamp":
                avg, var, end = self.avg_time(v)
                if var <= self.thld[0]:
                    ret['time'] = (avg, end)
            elif type(v[0]) is int:
                avg, var, med = self.avg_int(v)
                if var <= self.thld[1]:
                    ret[k] = (avg, med)
            elif type(v[0]) is str:
                avg, rat = self.avg_str(v)
                if rat >= self.thld[2]:
                    ret[k] = avg

        # return self.dict_to_log(ret)
        ret_list = []
        for k, v in ret.items():
            ret_list.append((k, v))
        return ret_list

    # pick representative logs
    def cluster_log(self, logs):
        x = np.arange(len(logs)).reshape(-1, 1)

        dbscan = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric=self.__dist__,
                        metric_params={'log': logs}).fit(x)
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

    # pick representative logs based on A priori algorithm
    def cluster_log2(self, logs):
        print(None)  # TODO: impl

    # return dense 1-region
    def get_dense_region(self, logs):
        regions = {}

        for log in logs:
            for point in log:
                interval = self.get_interval(point)
                for v in interval:
                    if v in regions:
                        regions[v] = regions[v] + 1
                    else:
                        regions[v] = 1

        for k in list(regions.keys()):
            if regions[k] < self.minsup:
                del regions[k]

        return regions

    # return candidate cluster
    def get_candidate_cluster(self, log):
        print(None)  # TODO: impl

    # returns acceptable region
    def get_interval(self, point):
        if self.is_time(point):
            time = self.time_to_ang(point[1])
            start = round((time - self.time_err) % 360)
            end = round((time + self.time_err) % 360)
            if start <= end:
                region = [('time', x) for x in range(start, end + 1)]
            else:
                region = [('time', x) for x in range(start, 360)]
                region = region + [('time', x) for x in range(0, end + 1)]
        elif self.is_int(point):
            start = point[1] - self.int_err
            end = point[1] + self.int_err
            region = [(point[0], x) for x in range(start, end + 1)]
        else:   # when point has string value
            region = [(point[0], point[1])]

        return region

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
            lg_list = list(i for i in lg.items() if i[0] != 'command')

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
        def ang_to_min(angle):
            day = 24 * 60
            minute = angle * day / 360
            if minute < 0:
                minute += day
            return divmod(minute, 60)

        frmt = '%H:%M'
        dts = [datetime.strptime(lg[11:16], frmt) for lg in logs]
        minutes = [dt.hour * 60 + dt.minute for dt in dts]

        # convert minutes to angle to calculate mean and variance
        day = 24 * 60
        angles = np.array([m * 360. / day for m in minutes]) * u.deg

        mean_angle = circmean(angles).value
        var = circvar(angles).value  # use angular variance

        mean_t = '%02i:%02i' % ang_to_min(mean_angle)
        min_t = '%02i:%02i' % ang_to_min(min(angles).value)
        max_t = '%02i:%02i' % ang_to_min(max(angles).value)

        return mean_t, var, (min_t, max_t)

    # return mode of string type values and ratio
    # assume two possible state
    @staticmethod
    def avg_str(logs):
        counter = Counter(logs).most_common(1)

        return counter[0][0], counter[0][1] / len(logs)

    # return mean and variance of integer type values
    @staticmethod
    def avg_int(logs):
        return np.mean(logs), np.var(logs), np.median(logs)

    # convert string type timestamp to angle
    @staticmethod
    def time_to_ang(log):
        frmt = '%H:%M'
        dt = datetime.strptime(log[11:16], frmt)
        minute = dt.hour * 60 + dt.minute

        return minute / 4

    # return true if point represents time attribute
    @staticmethod
    def is_time(point):
        return (point[0] == 'timestamp') or (point[0] == 'time')

    # return true if point has integer type value
    @staticmethod
    def is_int(point):
        return type(point[1]) == int
