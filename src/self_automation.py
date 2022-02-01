import json
from sklearn.cluster import DBSCAN


# generate rule and mode from logs
class SelfAutomation:
    # set hyper parameters
    def __init__(self):
        self.eps = 0.5
        self.min_samples = 3

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

            if cmd in log_cmd:
                log_cmd[cmd].append(lg)
            else:
                log_cmd[cmd] = [lg]

        return log_cmd

    # custom distance function
    def log_dist(self):
        return 0

    # pick representative logs
    def cluster_log(self, logs):

        clustering = DBSCAN(eps=self.eps, min_samples=self.min_samples, metric=self.log_dist).fit(logs)

        return logs[0]




