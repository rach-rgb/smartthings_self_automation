import unittest

from src.self_automation import SelfAutomation


# scenario tests
class TestScenario(unittest.TestCase):
    def setUp(self):
        self.automation = SelfAutomation()

    def test_simple(self):
        file_names = self.automation.run('simple.json')
        result = SelfAutomation.read_log('./output/simple_on_rule.json')
        gt = SelfAutomation.read_log('answer/simple_on_rule.json')

        self.assertEqual(1, len(file_names))
        self.assertEqual(gt, result)

    # generate rule for each command('on' and 'off)
    # generate EveryAction for time attribute
    def test_time(self):
        file_names = self.automation.run('time.json')
        result_1 = SelfAutomation.read_log('./output/time_on_rule.json')
        gt_1 = SelfAutomation.read_log('answer/time_on_rule.json')
        result_2 = SelfAutomation.read_log('./output/time_off_rule.json')
        gt_2 = SelfAutomation.read_log('answer/time_off_rule.json')

        self.assertEqual(2, len(file_names))
        self.assertEqual(gt_1, result_1)
        self.assertEqual(gt_2, result_2)

    # no rule is generated
    def test_noise(self):
        file_names = self.automation.run('noise.json')

        self.assertEqual(0, len(file_names))

    # # generate lessThan or greaterThan operation for integer attribute
    # def test_integer(self):
    #     file_names = self.automation.run('sensor_int.json')
    #     result_1 = SelfAutomation.read_log('./output/sensor_int_on_rule.json')
    #     gt_1 = SelfAutomation.read_log('answer/sensor_int_on_rule.json')
    #     result_2 = SelfAutomation.read_log('./output/sensor_int_off_rule.json')
    #     gt_2 = SelfAutomation.read_log('answer/sensor_int_off_rule.json')
    #
    #     self.assertEqual(2, len(file_names))
    #     self.assertEqual(gt_1, result_1)
    #     self.assertEqual(gt_2, result_2)

