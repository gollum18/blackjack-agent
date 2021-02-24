from bqa.qtable import QTable

import unittest


class TestQTable(unittest.TestCase):


    TEST_STATE = hash((1, 2, 3))
    TEST_WEIGHTS = [0.1, 0.3, 0.6]
    TEST_BIASES = [0.25, 0.25, 0.5]
    TEST_QVALUES = [1234, 5678, 4321]


    def test_eviction(self):
        pass


    def test_get(self):
        table = QTable()
        table.put(
            TestQTable.TEST_STATE,
            TestQTable.TEST_WEIGHTS,
            TestQTable.TEST_BIASES,
            TestQTable.TEST_QVALUES
        )
        weights, biases, qvalues = table.get(
            TestQTable.TEST_STATE
        )
        self.assertEqual(weights, TestQTable.TEST_WEIGHTS)
        self.assertEqual(biases, TestQTable.TEST_BIASES)
        self.assertEqual(qvalues, TestQTable.TEST_QVALUES)


    def test_put(self):
        table = QTable()
        table.put(
            TestQTable.TEST_STATE,
            TestQTable.TEST_WEIGHTS,
            TestQTable.TEST_BIASES,
            TestQTable.TEST_QVALUES
        )
        self.assertTrue(table.contains(TestQTable.TEST_STATE))


if __name__ == '__main__':
    unittest.main()
