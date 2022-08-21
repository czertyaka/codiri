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
        self.assertEqual(LazyEvaluation(lambda: None).exec(), None)
        self.assertEqual(LazyEvaluation(lambda: 1).exec(), 1)
        self.assertEqual(LazyEvaluation(lambda x: x).exec((1,)), 1)
        self.assertEqual(LazyEvaluation(lambda x: x**2).exec((2,)), 4)
        self.assertEqual(LazyEvaluation(lambda x, y: x**y).exec((2, 3)), 8)

    def test_exec_wrong_params(self):
        self.assertRaises(
            TypeError, lambda: LazyEvaluation(lambda: None).exec(1)
        )
        self.assertRaises(
            TypeError, lambda: LazyEvaluation(lambda: None).exec((1,))
        )
        self.assertRaises(
            TypeError, lambda: LazyEvaluation(lambda x: None).exec()
        )
        self.assertRaises(
            TypeError, lambda: LazyEvaluation(lambda x: None).exec((1, 2))
        )

    def test_cumulative_results(self):
        evalution = LazyEvaluation(lambda x: x**2)
        self.assertEqual(evalution.exec((1,)), 1)
        self.assertEqual(evalution.results, {(1,): 1})
        self.assertEqual(evalution.exec((2,)), 4)
        self.assertEqual(evalution.results, {(1,): 1, (2,): 4})
        self.assertEqual(evalution.exec((3,)), 9)
        self.assertEqual(evalution.results, {(1,): 1, (2,): 4, (3,): 9})

    def test_exec_with_same_args(self):
        mock = MagicMock(return_value=None)
        evalution = LazyEvaluation(mock)
        evalution.exec((1,))
        evalution.exec((1,))
        mock.assert_called_once_with(1)
        evalution.exec((2,))
        mock.assert_has_calls([call(1), call(2)])
        self.assertEqual(evalution.results, {(1,): None, (2,): None})
