from codiri.src.model.lazy_eval import LazyEvaluation
from unittest.mock import MagicMock, call
import unittest


class TestLazyEvaluation(unittest.TestCase):
    def test_do_not_exec_on_creation(self):
        self.assertEqual(LazyEvaluation(lambda: None).results, dict())
        self.assertEqual(LazyEvaluation(lambda: 1).results, dict())
        self.assertEqual(LazyEvaluation(lambda x: x).results, dict())
        self.assertEqual(LazyEvaluation(lambda x, y: x * y).results, dict())

    def test_exec(self):
        self.assertEqual(LazyEvaluation(lambda: None)(), None)
        self.assertEqual(LazyEvaluation(lambda: 1)(), 1)
        self.assertEqual(LazyEvaluation(lambda x: x)((1,)), 1)
        self.assertEqual(LazyEvaluation(lambda x: x**2)((2,)), 4)
        self.assertEqual(LazyEvaluation(lambda x, y: x**y)((2, 3)), 8)

    def test_exec_wrong_params(self):
        self.assertRaises(TypeError, lambda: LazyEvaluation(lambda: None)(1))
        self.assertRaises(
            TypeError, lambda: LazyEvaluation(lambda: None)((1,))
        )
        self.assertRaises(TypeError, lambda: LazyEvaluation(lambda x: None)())
        self.assertRaises(
            TypeError, lambda: LazyEvaluation(lambda x: None)((1, 2))
        )

    def test_cumulative_results(self):
        evalution = LazyEvaluation(lambda x: x**2)
        self.assertEqual(evalution((1,)), 1)
        self.assertEqual(evalution.results, {(1,): 1})
        self.assertEqual(evalution.result((1,)), 1)
        self.assertEqual(evalution((2,)), 4)
        self.assertEqual(evalution.results, {(1,): 1, (2,): 4})
        self.assertEqual(evalution.result((1,)), 1)
        self.assertEqual(evalution.result((2,)), 4)
        self.assertEqual(evalution((3,)), 9)
        self.assertEqual(evalution.results, {(1,): 1, (2,): 4, (3,): 9})
        self.assertEqual(evalution.result((1,)), 1)
        self.assertEqual(evalution.result((2,)), 4)
        self.assertEqual(evalution.result((3,)), 9)

    def test_exec_with_same_args(self):
        mock = MagicMock(return_value=None)
        evalution = LazyEvaluation(mock)
        evalution((1,))
        evalution((1,))
        mock.assert_called_once_with(1)
        evalution((2,))
        mock.assert_has_calls([call(1), call(2)])
        self.assertEqual(evalution.results, {(1,): None, (2,): None})
