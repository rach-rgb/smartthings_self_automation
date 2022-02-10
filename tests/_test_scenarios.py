from src.self_automation import SelfAutomation


# scenario test
class TestScenario:
    def __init__(self, input_dir, output_dir, answ_dir, logs, param=None):
        # create module
        self.automation = SelfAutomation(input_dir, param)
        # directory to store generated rules
        self.output_dir = output_dir
        # directory of ground truth rules
        self.answ_dir = answ_dir
        # file names to analyze
        self.logs = logs

    def run(self, verbose=True):
        total = 0
        correct = 0

        for log in self.logs:
            rets = self.automation.run(log, self.output_dir)

            # compare each result with ground truth rules
            for r in rets:
                expect = SelfAutomation.read_log(self.answ_dir+r)
                result = SelfAutomation.read_log(self.output_dir+r)

                if expect == result:
                    if verbose:
                        print('[correct] ', r)
                    correct = correct + 1
                else:
                    if verbose:
                        print('[fail] ', r)

            total = total + len(rets)

        score = correct/total*100

        if verbose:
            print('score: ', score)

        return score


if __name__ == '__main__':
    logs = ['time.json', 'time_noise.json', 'sensor_int.json', 'sensor_str.json', 'sensor_complex.json',
            'multiple_neighbor']
    testModule = TestScenario('./logs/', './output/', './rules/', logs)
    testModule.run(True)


