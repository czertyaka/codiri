from typing import Callable, Tuple


class LazyEvaluation:
    """Stores results of deferred computing expression for different params"""

    def __init__(self, formula: Callable):
        """Constructor
        :param formula: expression itself of callable type
        """
        self.__formula = formula
        self.__results = dict()

    def __call__(self, params: Tuple = tuple()):
        """Execute evaluation
        :param params: arguments expected by evaluation's formula
        :return: result of evluation for given arguments
        """
        if params not in self.__results.keys():
            self.__results[params] = self.__formula(*params)
        return self.__results[params]

    @property
    def results(self):
        """Get results of evaluation for each arguments set this instance were
        executed with
        """
        return self.__results
