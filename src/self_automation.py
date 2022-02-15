import json
import numpy as np
from datetime import datetime
from itertools import product


# generate rule and mode from logs
class SelfAutomation:
    def __init__(self, input_dir='./logs/', param=None):
        # set log directory and hyperparameters
        self.input_dir = input_dir
        if param is None:
            self.min_sup = 3     # minimum support
            self.time_err = 3.75    # acceptable error of time attribute as an angle, equivalent to 15 minutes
            self.int_err = 5    # acceptable error of integer attribute
        else:
            self.min_sup = param['min_sup']
            self.time_err = param['time_err']
            self.int_err = param['int_err']

    # export self-generated rules and return file names of exported rules as a list
    # file_in: directory to read logs, dir_out: directory to save generated rules
    def run(self, file_in, dir_out='./output/'):
        data = self.read_log(self.input_dir + file_in)

        if len(data['history']) < self.min_sup:
            print("No rule is detected")
            return []

        log_cls_cmd = self.cls_log(data['history'])

        file_names = []

        # generate rules for each device command
        for cmd in log_cls_cmd.keys():
            clusters = self.cluster_log(log_cls_cmd[cmd], info=True)
            if len(clusters) == 0:
                print("No rule is detected")

            # build rule for each cluster
            for idx, log in enumerate(clusters):
                rule = self.generate_rule(data, log, cmd)

                if len(clusters) == 1:
                    file_out = file_in.split('.')[0] + '_' + cmd + '_rule.json'
                else:
                    file_out = file_in.split('.')[0] + '_' + cmd + str(idx) + '_rule.json'
                file_names.append(file_out)

                with open(dir_out + file_out, 'w') as f:
                    json.dump(rule, f)

        return file_names

    # return rule built from data and cluster
    def generate_rule(self, data, cluster, cmd):
        neigh_dict = {n['device']: n for n in data['neighbors']}

        rule_name = self.construct_name(data['device'], neigh_dict.keys(), cmd)

        # create rule
        result = self.construct_result(data['device'], data['capability'], cmd)

        if len(cluster) == 1 and cluster[0][0] == 'time':
            # construct EveryAction if there's only time query
            action = self.construct_EveryAction(cluster[0], result)
        else:
            action = self.construct_IfAction(cluster, neigh_dict, result)

        return {'name': rule_name, 'actions': [action]}

    # return name of rule
    @staticmethod
    def construct_name(device, neighbors, cmd):
        name = device
        for n in neighbors:
            name = name + '-' + n
        return name + '-' + cmd

    # return result of rule ('then' part)
    @staticmethod
    def construct_result(device, cap, cmd):
        action = [{'command': {"devices": [device], 'commands': [{'capability': cap, 'command': cmd}]}}]
        return action

    # return time operation with 'between'
    # query given with form ('time', (cluster, (start, end)))
    @staticmethod
    def time_operation(query):
        start = query[1][1][0]
        end = query[1][1][1]
        return {'between': {'value': {'time': {'reference': 'Now'}},
                            'start': {'time': {'hour':  int(start[0:2]), 'minute': int(start[3:5])}},
                            'end': {'time': {'hour': int(end[0:2]), 'minute': int(end[3:5])}}}}

    # return integer related operation
    # query given with ('device', (cluster, mean))
    @staticmethod
    def integer_operation(query, attr):
        if query[1][0] < query[1][1]:
            # use 'greater_than' syntax if center <= mean
            op = 'greater_than'
        else:
            # use 'less_than' syntax if center > mean
            op = 'less_than'
        return {op: {"left": {"device": {"devices": [query[0].split(':')[0]], "attribute": attr}},
                     "right": {"integer": query[1][0]}}}

    # return string related operation
    # query given with ('device', value)
    @staticmethod
    def string_operation(query, attr):
        operation = {"equals": {"left": {"device": {"devices": [query[0].split(':')[0]], "attribute": attr}},
                                "right": {"string": query[1]}}}
        return operation

    # return condition in EveryAction format
    @staticmethod
    def construct_EveryAction(time_query, result):
        hour = int(time_query[1][0][0:2])
        minute = int(time_query[1][0][3:5])
        operation = {'time': {'hour': hour, 'minute': minute}}

        return {'every': {'specific': operation, 'actions': result}}

    # return condition in IfAction format
    def construct_IfAction(self, queries, devices, result):
        operations = []
        for q in queries:
            if self.is_time(q):
                operations.append(self.time_operation(q))
            else:
                info = q[0].split(':')
                attr = devices[info[0]]['value'][int(info[1])]['attribute']
                if self.is_int(q):
                    operations.append(self.integer_operation(q, attr))
                else:
                    operations.append(self.string_operation(q, attr))

        # merge operations
        if len(operations) == 1:
            operations[0]['then'] = result
            action = {'if': operations[0]}
        else:
            action = {'if': {'and': []}}
            for op in operations:
                action['if']['and'].append(op)
            action['if']['then'] = result

        return action

    # return representative logs based on apriori algorithm
    def cluster_log(self, logs, info=False):
        one_region = list(self.get_dense_region(logs))

        cand_dict = {}
        for idx, log in enumerate(logs):
            attributes = [self.get_interval(attr) for attr in log]
            full_logs = list(product(*attributes))

            cands = [self.get_candidate_cluster(one_region, lg) for lg in full_logs]
            for c in cands:
                key = tuple(c)
                if key in cand_dict:
                    cand_dict[key].append(idx)
                elif key != ():
                    cand_dict[key] = [idx]

        for key in list(cand_dict.keys()):
            if len(cand_dict[key]) < self.min_sup:
                del cand_dict[key]

            attributes = [self.get_interval(attr) for attr in key]
            for near_key in list(product(*attributes)):
                if (near_key in cand_dict) and (len(cand_dict[key]) < len(cand_dict[near_key])):
                    del cand_dict[key]
                    break

        clusters = []
        if not info:
            clusters = []
            for key in cand_dict.keys():
                if self.is_time(key[0]):
                    clusters.append((('time', self.ang_to_min(key[0][1])), ) + key[1:])
                else:
                    clusters.append(key)
        else:
            for key in cand_dict.keys():
                contribute = [logs[idx] for idx in set(cand_dict[key])]
                clusters.append(self.add_info(contribute, key))

        return clusters

    # return dense 1-region dictionary
    def get_dense_region(self, logs):
        regions = {}

        for log in logs:
            for point in log:
                interval = self.get_interval(point)
                for v in interval:
                    if v in regions:
                        regions[v] = regions[v] + 0.5
                    else:
                        regions[v] = 0.5
        for k in list(regions.keys()):
            if regions[k] < self.min_sup:
                del regions[k]

        return regions

    # returns acceptable region
    def get_interval(self, point):
        if self.is_time(point):
            if type(point[1]) is str:
                time = self.time_to_ang(point[1])
            else:
                time = point[1]
            start = round((time - self.time_err) % 360)
            end = round((time + self.time_err) % 360)
            if start <= end:
                region = [('time', x) for x in range(start, end + 1)]
            else:
                region = [('time', x) for x in range(start, 360)]
                region = region + [('time', x) for x in range(0, end + 1)]
            region.append(('time', round(time)))
        elif self.is_int(point):
            start = point[1] - self.int_err
            end = point[1] + self.int_err
            region = [(point[0], x) for x in range(start, end + 1)]
            region.append(point)
        else:   # when point has string value
            region = [point, point]

        return region

    # append additional information to cluster
    def add_info(self, logs, center):
        data = self.logs_to_dict(logs)

        ret = {}
        for k, v in data.items():
            if k == 'timestamp':
                ret['time'] = self.time_info(v)
            elif type(v[0]) == int:
                me = self.int_info(v)
                ret[k] = round(me, 2)

        new_center = []
        for query in center:
            if self.is_time(query):
                value = (self.ang_to_min(query[1]), ret['time'])
                new_center.append(('time', value))
            elif self.is_int(query):
                value = (query[1], ret[query[0]])
                new_center.append((query[0], value))
            else:
                new_center.append(query)

        return tuple(new_center)

    # return candidate cluster
    # time attribute has angle form
    @staticmethod
    def get_candidate_cluster(regions, log):
        candidate = []
        for point in log:
            if point in regions:
                candidate.append(point)
        return candidate

    # return usage log as a dictionary
    @staticmethod
    def read_log(file_name):
        try:
            with open(file_name, "r") as f:
                data = json.load(f)
            return data
        except FileNotFoundError as e:
            print(e)
            return None

    # return a dictionary of logs,
    # using 'command' as a key and a list of corresponding logs as a value
    @staticmethod
    def cls_log(logs):
        log_cls_cmd = {}
        for lg in logs:
            cmd = lg['command']

            # exclude value of 'command' from list
            lg_list = []
            for k, v in lg.items():
                if type(v) is list:
                    for idx, elem in enumerate(v):
                        lg_list.append((k+":"+str(idx), elem))
                elif k != 'command':
                    lg_list.append((k, v))

            if cmd in log_cls_cmd:
                log_cls_cmd[cmd].append(lg_list)
            else:
                log_cls_cmd[cmd] = [lg_list]

        return log_cls_cmd

    # return a dictionary using a name of an attribute as a key and
    # a list of corresponding values as a value
    @staticmethod
    def logs_to_dict(logs):
        log_dict = {}

        # create key and value
        for attr in logs[0]:
            if type(attr[1]) is list:  # split the list and name each attribute as 'device-name' + count
                for i in range(0, len(attr[1])):
                    log_dict[attr[0] + ':' + str(i)] = [attr[1][i]]
            else:
                log_dict[attr[0]] = [attr[1]]

        if len(logs) > 1:
            for log in logs[1:]:
                for attr in log:
                    if type(attr[1]) is list:
                        for i in range(0, len(attr[1])):
                            log_dict[attr[0] + ':' + str(i)].append(attr[1][i])
                    else:
                        log_dict[attr[0]].append(attr[1])

        return log_dict

    # return true if point represents time attribute
    @staticmethod
    def is_time(point):
        return (point[0] == 'timestamp') or (point[0] == 'time')

    # return true if point has integer type value
    @staticmethod
    def is_int(point):
        return (type(point[1]) == int) or (type(point[1][0]) == int)

    # convert angle as string type time
    @staticmethod
    def ang_to_min(angle):
        day = 24 * 60
        minute = angle * 4
        if minute >= day:
            minute -= day
        return '%02i:%02i' % divmod(minute, 60)

    # convert string type time to angle
    @staticmethod
    def time_to_ang(str_time):
        frmt = '%H:%M'
        dt = datetime.strptime(str_time[11:16], frmt)
        minute = dt.hour * 60 + dt.minute

        return minute / 4

    # return minimum and maximum of time
    @staticmethod
    def time_info(logs):
        # convert minutes to angle
        angles = [SelfAutomation.time_to_ang(m) for m in logs]

        min_t = SelfAutomation.ang_to_min(min(angles))
        max_t = SelfAutomation.ang_to_min(max(angles))

        return min_t, max_t

    # return mean of integer values
    @staticmethod
    def int_info(logs):
        return np.mean(logs)

