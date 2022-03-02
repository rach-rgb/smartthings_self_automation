import json
import numpy as np
from datetime import datetime
from collections import Counter


# generate rule from logs
class SelfAutomation:
    INTMAX = 987654321

    def __init__(self, input_dir='./logs/', param=None):
        # set directory and hyperparameters
        self.input_dir = input_dir
        if param is None:
            self.min_sup = 5  # minimum support
            self.time_err = 3.75  # acceptable error of time component as an angle, equivalent to 15 minutes
            self.num_err = 5  # acceptable error of integer component
        else:
            self.min_sup = param['min_sup']
            self.time_err = param['time_err']
            self.num_err = param['int_err']

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

    # Rule Generating
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
    # query given with form ('time', (mode, (min, max)))
    @staticmethod
    def time_operation(query):
        start = query[1][1][0]
        end = query[1][1][1]
        return {'between': {'value': {'time': {'reference': 'Now'}},
                            'start': {'time': {'hour': int(start[0:2]), 'minute': int(start[3:5])}},
                            'end': {'time': {'hour': int(end[0:2]), 'minute': int(end[3:5])}}}}

    # return numerical related operation
    # query given with ({neighbor_device}, (mode, mean))
    @staticmethod
    def numeric_operation(query, attr):
        if query[1][0] < query[1][1]:
            # use 'greater_than' syntax if center <= mean
            op = 'greater_than'
        else:
            # use 'less_than' syntax if center > mean
            op = 'less_than'
        return {op: {"left": {"device": {"devices": [query[0].split(':')[0]], "attribute": attr}},
                     "right": {"integer": query[1][0]}}}

    # return string related operation
    # query given with ({neighbor_device}, value)
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
                attr = devices[info[0]]['value'][int(info[1])]['attribute'] # retrieve device information
                if self.is_numeric(q):
                    operations.append(self.numeric_operation(q, attr))
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

    # Log Clustering
    # return representative logs based on SLCT algorithm
    def cluster_log(self, logs, info=False):
        # return index of val using start of interval
        def find_interval(key, start, end, target):
            if start >= end:  # no interval
                return -1

            cur = int((start + end) / 2)

            if dense_one_regions[key][cur][0] == target:
                return cur
            elif target < dense_one_regions[key][cur][0]:
                return find_interval(key, start, cur, target)
            else:  # dense_one_regions[k][cur][-1] < target
                return find_interval(key, cur + 1, end, target)

        dense_one_regions = self.get_dense_region(logs)

        cand_dict = {}
        for log in logs:
            candidate = tuple(self.get_candidate_cluster(dense_one_regions, log))

            if candidate in cand_dict:
                cand_dict[candidate] = cand_dict[candidate] + 1
            elif candidate != ():
                cand_dict[candidate] = 1

        clusters = []
        for candidate in cand_dict.keys():
            if cand_dict[candidate] >= self.min_sup:
                # format cluster
                center = []
                for comp in candidate:
                    if self.is_time(comp):
                        idx = find_interval(comp[0], 0, len(dense_one_regions[comp[0]]), comp[1][0])
                        intv = dense_one_regions[comp[0]][idx]
                        common = self.most_frequent(intv, True)
                        if not info:
                            center.append(('time', self.ang_to_time(common)))
                        else:
                            center.append(('time', (self.ang_to_time(common),


                                                    (self.ang_to_time(intv[0]), self.ang_to_time(intv[-1])))))
                    elif self.is_numeric(comp):
                        idx = find_interval(comp[0], 0, len(dense_one_regions[comp[0]]), comp[1][0])
                        intv = dense_one_regions[comp[0]][idx]
                        common = self.most_frequent(intv)
                        if not info:
                            center.append((comp[0], common))
                        else:
                            center.append((comp[0], (common, np.mean(intv))))
                    else:  # string component
                        center.append(comp)
                clusters.append(tuple(center))

        return clusters

    # return dense 1-region dictionary
    # key: name of component, value: list of dense region
    def get_dense_region(self, logs):
        dense_one_dict = {}

        for key, val in self.logs_to_dict(logs).items():
            category = key

            if self.is_time((key, val[0])):
                category = 'time'
                dense_regions = self.get_time_regions(val)
            elif self.is_numeric((key, val[0])):
                dense_regions = self.get_numeric_regions(val)
            else:  # string features
                dense_regions = self.get_string_regions(val)

            if len(dense_regions) > 0:
                dense_one_dict[category] = dense_regions

        return dense_one_dict

    # return dense 1-regions of time components
    def get_time_regions(self, components):
        dense_regions = []

        angles = sorted(components)

        # count frequency of each interval
        first_intv = None
        prev = angles[0]
        intv = []
        for v in angles:
            if v <= prev + self.time_err:  # belongs to same interval
                prev = v
                intv.append(v)
            else:  # create new interval
                if intv[0] == angles[0]:  # keep information of first interval
                    first_intv = intv
                elif len(intv) >= self.min_sup:  # add interval to dense region
                    dense_regions.append(intv)
                prev = v
                intv = [v]

        # process first and last interval
        if first_intv is not None:
            end = intv[-1] + self.time_err  # end of last interval
            # first interval and last interval need to be merged
            if end >= 360 and (end - 360) >= first_intv[0]:
                if len(first_intv) + len(intv) >= self.min_sup:
                    dense_regions.append(intv + first_intv)
            else:
                if len(first_intv) >= self.min_sup:
                    dense_regions.insert(0, first_intv)
                if len(intv) >= self.min_sup:
                    dense_regions.append(intv)
        else:   # found only one interval in components
            if len(intv) >= self.min_sup:
                dense_regions.append(intv)

        return dense_regions

    # get dense regions of numeric type component
    def get_numeric_regions(self, components):
        dense_regions = []

        components = sorted(components)
        components.append(components[-1] + SelfAutomation.INTMAX)

        # count frequency of each interval
        prev = components[0]
        intv = []
        for v in components:
            if v <= prev + self.num_err:  # belongs to same interval
                prev = v
                intv.append(v)
            else:  # create new interval
                if len(intv) >= self.min_sup:  # add interval to dense region
                    dense_regions.append(intv)
                prev = v
                intv = [v]

        if len(intv) >= self.min_sup:
            dense_regions.append(intv)

        return dense_regions

    # get dense regions of string type features
    def get_string_regions(self, values):
        dense_regions = []

        c = Counter(values)

        for k, v in c.items():
            if v >= self.min_sup:
                dense_regions.append(k)

        return dense_regions

    # return cluster candidate
    # time and numeric component returns dense region as interval
    def get_candidate_cluster(self, dense_regions, log):
        # return index of interval containing val
        def find_intv(start, end):
            if start >= end:  # no interval
                return -1

            cur = int((start + end) / 2)

            if regions[cur][0] <= val <= regions[cur][-1]:
                return cur
            elif val < regions[cur][0]:
                return find_intv(start, cur)
            else:
                return find_intv(cur + 1, end)

        candidate = []

        for comp in log:
            key = comp[0]
            val = comp[1]

            if self.is_time(comp):
                if 'time' in dense_regions:
                    total_regions = dense_regions['time']   # entire regions for time component
                    if total_regions[-1][0] > total_regions[-1][-1]:    # last interval is date changing interval
                        if val <= total_regions[-1][-1] or total_regions[-1][0] <= val:
                            candidate.append(('time', (total_regions[-1][0], total_regions[-1][-1])))
                            continue
                        else:
                            regions = total_regions[0:-1]   # remove date changing interval
                    else:
                        regions = total_regions
                    idx = find_intv(0, len(regions))
                    if idx != -1:
                        candidate.append(('time', (regions[idx][0], regions[idx][-1])))
            elif self.is_numeric(comp):
                if key in dense_regions:
                    regions = dense_regions[key]
                    # find interval
                    idx = find_intv(0, len(regions))
                    if idx != -1:
                        candidate.append((key, (regions[idx][0], regions[idx][-1])))
            else:  # string type component
                if (key in dense_regions) and (val in dense_regions[key]):
                    candidate.append((key, val))

        return candidate

    # return most frequent value in ary
    # if tie exists, return the value which is closest to mean
    @staticmethod
    def most_frequent(ary, is_time=False):
        if is_time and ary[0] > ary[-1]:    # date changing interval
            new_ary = []
            for v in ary:
                new_ary.append(v-ary[0])
                if v < ary[0]:
                    new_ary[-1] += 360
            return (SelfAutomation.most_frequent(new_ary) + ary[0]) % 360

        cands = []

        c = Counter(ary)
        for key in c:
            if c[key] == max(c.values()):
                cands.append(key)

        if len(cands) == 1:
            return cands[0]
        else:
            mean = np.mean(ary)
            diff = SelfAutomation.INTMAX
            val = None
            for v in cands:
                if abs(v - mean) < diff:
                    diff = abs(v-mean)
                    val = v
            return val

    # Helper Functions
    # return device usage logs as a dictionary
    @staticmethod
    def read_log(file_name):
        try:
            with open(file_name, "r") as f:
                data = json.load(f)
            return data
        except FileNotFoundError as e:
            print(e)
            return None

    # return a dictionary of formatted logs
    # key: command, 'value': list of corresponding logs
    @staticmethod
    def cls_log(logs):
        log_cmd_dict = {}
        for log in logs:
            cmd = log['command']

            new_log = []
            for k, v in log.items():
                # convert time component to angle representation
                if SelfAutomation.is_time([k, v]):
                    new_log.append(('time', SelfAutomation.time_to_ang(v)))
                # split the list and name each component as "device_name:index"
                elif type(v) is list:
                    for idx, elem in enumerate(v):
                        new_log.append((k + ":" + str(idx), elem))
                # remove command component
                elif k != 'command':
                    new_log.append((k, v))

            if cmd in log_cmd_dict:
                log_cmd_dict[cmd].append(new_log)
            else:
                log_cmd_dict[cmd] = [new_log]

        return log_cmd_dict

    # return a dictionary summarizing entire input logs
    # key: name of a component, value: list of values corresponding to a key
    @staticmethod
    def logs_to_dict(logs):
        log_dict = {}

        # register key
        for comp in logs[0]:
            log_dict[comp[0]] = [comp[1]]

        if len(logs) > 1:
            for log in logs[1:]:
                for comp in log:
                    log_dict[comp[0]].append(comp[1])

        return log_dict

    # return true if point represents time component
    @staticmethod
    def is_time(point):
        return (point[0] == 'timestamp') or (point[0] == 'time')

    # return true if point represents numerical component
    @staticmethod
    def is_numeric(point):
        return isinstance(point[1], (int, float, complex)) or isinstance(point[1][0], (int, float, complex))

    # convert string representation of time to angle
    @staticmethod
    def time_to_ang(str_time):
        frmt = '%H:%M'
        dt = datetime.strptime(str_time[11:16], frmt)

        return (dt.hour * 60 + dt.minute) / 4

    # convert angle to string representation of time
    @staticmethod
    def ang_to_time(angle):
        minute = angle * 4
        if minute >= 1440:
            minute -= 1440
        return '%02i:%02i' % divmod(minute, 60)
