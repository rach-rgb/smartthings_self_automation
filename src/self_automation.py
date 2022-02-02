import json
import numpy as np
from datetime import datetime
from sklearn.cluster import DBSCAN


# generate rule and mode from logs
class SelfAutomation:
    # set hyper parameters
    def __init__(self):
        self.eps = 0.5
        self.min_samples = 3
        self.weight = [0.01, 1, 10]
        self.str_0 = ["OFF", 'off', 'inactive', "INACTIVE", 'sleep']
        self.str_1 = ["ON", 'on', 'active', "ACTIVE", 'awake']

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

                dist = dist + time.seconds/60 * self.weight[0]
            else:
                for k in range(0, len(x[i][1])):
                    x_val = x[i][1][k]
                    y_val = y[i][1][k]
                    if type(x_val) is int:
                        dist = dist + abs(x_val - y_val) * self.weight[1]
                    elif type(x_val) is str:
                        if x_val is not y_val:
                            dist = dist + 1 * self.weight[2]
        return dist

    # pick representative logs
    def cluster_log(self, logs):
        x = np.arange(len(logs)).reshape(-1, 1)
        labels = DBSCAN(eps=3, min_samples=3, metric=self.log_dist).fit(x)

        return []




