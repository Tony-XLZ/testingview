import warnings
from itertools import chain
from numbers import Number
from abc import abstractmethod, ABC
from copy import copy

import numpy as np
import pandas as pd


class StrategyBase(ABC):
    """
    A strategy base abstract class. Extend this class and
    override methods 'set_indicators()' and 'next()'
    to define your own strategy. Receives 'data'.

    'data' have to be a carefully
    stripped pandas.DataFrame with columns:
    'open', 'high', 'low', 'close' and 'volume'.

    Data index should be ascending datetime.
    """
    def __init__(self, data):  # I.
        # Check the format of data
        if not isinstance(data, pd.DataFrame):
            raise TypeError("data must be a pandas.DataFrame with columns")
        if len(data.columns.intersection({'open', 'high', 'low', 'close', 'volume'})) != 5:
            raise ValueError("data must be a pandas.DataFrame with columns "
                             "'open', 'high', 'low', 'close' and 'volume'(Case sensitive)")
        if data[['open', 'high', 'low', 'close', 'volume']].isnull().values.any():
            raise ValueError("Some ohlc values are missing (NaN). "
                             "Please strip those lines with 'df.dropna()' or "
                             "fill them in with 'df.fillna()' or whatever.")
        if not isinstance(data.index, pd.DatetimeIndex):
            raise ValueError('Data index is not datetime.')
        if not data.index.is_monotonic_increasing:
            warnings.warn('Data index is not sorted in ascending order. Automatically Sorted.',
                          stacklevel=2)
            data = data.sort_index()

        self._indicators = []
        self._data = data
        self.__data = data

    # Create a data property which is not private
    @property
    def data(self):
        """
        data for backtesting
        """
        return self._data

    # I. I read through the advanced framework Backtrader where data are transferred into line objects.
    # Inspired by Backtrader, this function is written on my own. Backtrader GitHub:
    # https://github.com/mementum/backtrader
    def ind(self, func, *args, **kwargs):
        """
        Declare indicator. An indicator is an array of values.
        Returns 'np.ndarray' of indicator values.

        'func' is a function that returns the indicator array of
        same length as 'strategybase.StrategyBase.data'.

        Additional '*args' and '**kwargs' are passed to 'func' and can
        be used for parameters.

        For example, using SMA function from TA-Lib:

            def set_indicators():
                self.sma5 = self.ind(ta.SMA, self.data.close, 5)
        """

        # create a method to return name of an indicator function
        # and data structure passed to the name of the indicator
        def _name_str(value):
            if isinstance(value, (Number, str)):
                return str(value)
            if isinstance(value, pd.DataFrame):
                return 'df'

            name = str(getattr(value, 'name', '') or '')
            # for name in 'ohlcv', create abbr.
            if name in ('open', 'high', 'low', 'close', 'volume'):
                return name[:1]
            if callable(value):
                name = getattr(value, '__name__', value.__class__.__name__)
            if len(name) > 10:
                name = name[:9] + '…'
            return name

        # Generate the name of the indicator for the legends of plotting
        params = ','.join(filter(None, map(_name_str, chain(args, kwargs.values()))))
        func_name = _name_str(func)
        name = (f'{func_name}({params})' if params else f'{func_name}')

        # Debug if func can run
        try:
            value = func(*args, **kwargs)
        except Exception as e:
            raise RuntimeError(f'Indicator "{name}" errored with exception: {e}')

        # When input is VALID, flip the value to get an arraylike structure
        if isinstance(value, pd.DataFrame):
            value = value.values.T

        # Transfer value into a ndarray
        if value is not None:
            try:
                value = np.asarray(value)
            except Exception:
                value = None

        is_arraylike = value is not None

        # Flip the array back
        if is_arraylike and np.argmax(value.shape) == 0:
            value = value.T

        # Check whether the indicator is valid
        if not is_arraylike or value.shape[-1] != len(self._data.close):
            raise ValueError(
                'Indicators must return numpy.arrays of same '
                f'length as data (data shape: {self._data.close.shape}; indicator "{name}"'
                f'shape: {getattr(value, "shape", "")}, returned value: {value})')

        # Add indicators into a list for later use
        if len(value) == len(self.__data):
            self._indicators.append(pd.DataFrame(value, index=self.data.index, columns=[name]))
            self._data = pd.concat([self._data, pd.DataFrame(value, index=self.data.index, columns=[name])],
                                   axis=1, ignore_index=False)
        return value

    @classmethod
    def crossover(cls, series1, series2):  # I.
        """
        Return 'True' if 'series1' just crossed over
        'series2'.
        """
        series1 = (series1.values if isinstance(series1, pd.Series) else series1)
        series2 = (series2.values if isinstance(series2, pd.Series) else series2)

        if series1[-2] < series2[-2] and series1[-1] > series2[-1]:
            return True

    @classmethod
    def long(cls):  # I.
        """
        Place a long order when the position is not long.
        """
        return 1

    @classmethod
    def offset(cls):  # I.
        """
        Offset positions.
        """
        return 0

    @classmethod
    def short(cls):  # I.
        """
        Place a short order when the position is not short.
        """
        return -1

    @abstractmethod
    def set_indicators(self):  # I.
        """
        Create indicators to construct your strategy.
        Override this method.
        """
        pass

    @abstractmethod
    def next(self):  # I.
        """
        Main strategy 'event_driven' method.
        This is the main method where strategy decisions
        upon indicators created in 'strategybase.StrategyBase.set_indicators()'
        take place.
        Override this method.
        """
        pass

    # Core loop to go through the data with strategy defined
    # It would generate signal which would pass into 'StrategyRun.BacktestRun'
    def _sig(self):  # I. I tried a lot of ways to construct the loop, this works well, but not debugged thoroughly.
        # create a copy so the loop can work properly
        _d_f = copy(self._data)
        siglist = [None, None]
        length = len(self._data)
        for i in range(2, length):
            self._data = _d_f.iloc[:i + 1, ]
            self.set_indicators()
            siglist.append(self.next())
        return siglist


# P.S.:
# I. My work and entirely original code
# II. Based on an existing source which has then been adapted to some degree
# III. Entirely copied from an existing source
