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

    # no rule is generated
    def test_noise(self):
        file_names = self.automation.run('noise.json')

        self.assertEqual(0, len(file_names))

    # there's enough history
    def test_not_enough(self):
        file_names = self.automation.run('not_enough.json')

        self.assertEqual(0, len(file_names))

    # multiple cluster for one command
    def test_multiple(self):
        file_names = self.automation.run('multiple.json')
        result_1 = SelfAutomation.read_log('./output/multiple_on0_rule.json')
        gt_1 = SelfAutomation.read_log('./output/multiple_on0_rule.json')
        result_2 = SelfAutomation.read_log('./output/multiple_on1_rule.json')
        gt_2 = SelfAutomation.read_log('./output/multiple_on1_rule.json')

        self.assertEqual(2, len(file_names))
        if gt_1 == result_1:
            self.assertEqual(gt_2, result_2)
        elif gt_2 == result_1:
            self.assertEqual(gt_1, result_2)
        else:
            self.assertTrue(0)

    # generate rule for each command('on' and 'off)
    # generate EveryAction for time component
    def test_time(self):
        file_names = self.automation.run('time.json')
        result_1 = SelfAutomation.read_log('./output/time_on_rule.json')
        gt_1 = SelfAutomation.read_log('answer/time_on_rule.json')
        result_2 = SelfAutomation.read_log('./output/time_off_rule.json')
        gt_2 = SelfAutomation.read_log('answer/time_off_rule.json')

        self.assertEqual(2, len(file_names))
        self.assertEqual(gt_1, result_1)
        self.assertEqual(gt_2, result_2)

    # generate lessThan or greaterThan condition for numeric component
    def test_numeric(self):
        file_names = self.automation.run('sensor_int.json')
        result_1 = SelfAutomation.read_log('./output/sensor_int_on_rule.json')
        gt_1 = SelfAutomation.read_log('answer/sensor_int_on_rule.json')
        result_2 = SelfAutomation.read_log('./output/sensor_int_off_rule.json')
        gt_2 = SelfAutomation.read_log('answer/sensor_int_off_rule.json')

        self.assertEqual(2, len(file_names))
        self.assertEqual(gt_1, result_1)
        self.assertEqual(gt_2, result_2)

    # generate equal operation for string component
    # generate between operation to combine time component
    def test_str(self):
        file_names = self.automation.run('sensor_str.json')
        result_1 = SelfAutomation.read_log('./output/sensor_str_on_rule.json')
        gt_1 = SelfAutomation.read_log('answer/sensor_str_on_rule.json')
        result_2 = SelfAutomation.read_log('./output/sensor_str_off_rule.json')
        gt_2 = SelfAutomation.read_log('./answer/sensor_str_off_rule.json')

        self.assertEqual(2, len(file_names))
        self.assertEqual(gt_1, result_1)
        self.assertEqual(gt_2, result_2)

    # related device holds more than one value
    def test_sensor_complex(self):
        self.automation.run('sensor_complex.json')
        result = SelfAutomation.read_log('./output/sensor_complex_on_rule.json')
        gt = SelfAutomation.read_log('answer/sensor_complex_on_rule.json')

        self.assertEqual(gt, result)

    # there are two devices
    def test_multiple_neighbor(self):
        file_names = self.automation.run('multiple_neighbor.json')
        result_1 = SelfAutomation.read_log('./output/multiple_neighbor_on_rule.json')
        gt_1 = SelfAutomation.read_log('answer/multiple_neighbor_on_rule.json')

        self.assertEqual(1, len(file_names))
        self.assertEqual(result_1, gt_1)
