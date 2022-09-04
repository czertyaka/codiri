from typing import Callable, Tuple, Dict


class LazyEvaluation:
    """Stores results of deferred computing expression for different params"""

    def __init__(self, formula: Callable):
        """Constructor

        Args:
            formula (Callable): expression itself
        """
        self.__formula = formula
        self.__results = dict()

    def __call__(self, params: Tuple = tuple()):
        """Execute evaluation

        Args:
            params (Tuple, optional): arguments expected by evaluation's
                formula

        Returns:
            TYPE: result of evaluation execution for given arguments
        """
        if params not in self.__results.keys():
            self.__results[params] = self.__formula(*params)
        return self.__results[params]

    @property
    def results(self) -> Dict:
        """Get results of evaluation for each arguments set this instance were
        executed with

        Returns:
            Dict: results of evaluation for each arguments set
        """
        return self.__results
