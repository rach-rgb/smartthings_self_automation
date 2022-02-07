import json
from itertools import product
from src.self_automation import SelfAutomation


class ParameterTesting:
    def __init__(self, test_file, eps, min_samples, wtime, wint, wstr, ttime, tint, tstr):
        self.test_file = test_file
        self.params_list = list(product(eps, min_samples, wtime, wint, wstr, ttime, tint, tstr))

    def grid_search(self):
        # load test cases
        test_cases = self.load_input()

        max_score = 0
        best_params = self.params_list[0]

        # evaluate each parameters
        for idx, p in enumerate(self.params_list):
            correct = 0
            module = self.__construct__(p)
            for logs, log in test_cases:
                if self.__test__(logs, log, module) is True:
                    correct = correct + 1
            if correct > max_score:
                max_score = correct
                best_params = p

        return max_score/len(test_cases)*100, best_params

    def load_input(self):
        with open(self.test_file, "r") as f:
            file = json.load(f)
        return file['test_cases']

    @staticmethod
    def __construct__(plist):
        param = {'eps': plist[0], 'min_samples': plist[1],
                 'wtime': plist[2], 'wint': plist[3], 'wstr': plist[4],
                 'ttime': plist[5], 'tint': plist[6], 'tstr': plist[7]}
        return SelfAutomation(param=param)

    @staticmethod
    def __test__(logs, log, module):
        return log == str(module.cluster_log(logs))


if __name__ == "__main__":
    eps = [720]
    min_samples = [3]
    weight_time = [1]
    weight_int = [3]
    weight_str = [180]
    thld_time = [0.001]
    thld_int = [15]
    thld_str = [0.8]

    test = ParameterTesting('cluster_sample', eps, min_samples, weight_time, weight_int, weight_str,
                            thld_time, thld_int, thld_str)
    score, param = test.grid_search()
    print('max score: ', score)
    print('eps: ', param[0], 'min_samples: ', param[1], 'wtime: ', param[2], 'wint: ', param[3], 'wstr: ', param[4],
          'ttime: ', param[5], 'tint: ', param[6], 'tstr: ', param[7])
