# This is a collection of 'simple_example.py' and 'advanced_examples.py'
# Interpretation of strategies and results are within README
from testingview import StrategyBase, BacktestRun
from testingview import yahoo_data, crypto_data

import numpy as np
import talib as ta


class SMA(StrategyBase):

    def set_indicators(self):
        self.sma5 = self.ind(ta.SMA, self.data.close, 5)
        self.sma20 = self.ind(ta.SMA, self.data.close, 20)

    def next(self):
        if self.crossover(self.sma5, self.sma20):
            return self.long()
        elif self.crossover(self.sma20, self.sma5):
            return self.short()


class MACD(StrategyBase):

    @staticmethod
    def macd(_df):
        k = _df.ewm(span=12, adjust=False, min_periods=12).mean()
        d = _df.ewm(span=26, adjust=False, min_periods=26).mean()
        return k - d

    @staticmethod
    def macd_s(_df):
        k = _df.ewm(span=12, adjust=False, min_periods=12).mean()
        d = _df.ewm(span=26, adjust=False, min_periods=26).mean()
        s = (k - d).ewm(span=9, adjust=False, min_periods=9).mean()
        return s

    @staticmethod
    def macd_h(_df):
        k = _df.ewm(span=12, adjust=False, min_periods=12).mean()
        d = _df.ewm(span=26, adjust=False, min_periods=26).mean()
        s = (k - d).ewm(span=9, adjust=False, min_periods=9).mean()
        return k - d - s

    def set_indicators(self):
        self.MACD = self.ind(self.macd, self.data.close)
        self.MACDsignal = self.ind(self.macd_s, self.data.close)
        # self.MACDhist = self.ind(self.macd_h, self.data.close)

    def next(self):
        if self.crossover(self.MACD, self.MACDsignal):
            return self.long()
        elif self.crossover(self.MACDsignal, self.MACD):
            return self.short()


class DaulThrust(StrategyBase):

    @staticmethod
    def upper_bound(_df):
        hh = _df.high.rolling(window=3).max()
        hc = _df.close.rolling(window=3).max()
        lc = _df.close.rolling(window=3).min()
        ll = _df.low.rolling(window=3).min()

        return _df.open + 0.5 * np.maximum(hh - lc, hc - ll)

    @staticmethod
    def lower_bound(_df):
        hh = _df.high.rolling(window=3).max()
        hc = _df.close.rolling(window=3).max()
        lc = _df.close.rolling(window=3).min()
        ll = _df.low.rolling(window=3).min()

        # ValueError when using max(hh - lc, hc - ll), please follow the pandas rule
        return _df.open - 0.3 * np.maximum(hh - lc, hc - ll)

    @staticmethod
    def close(_df):
        return _df.close

    def set_indicators(self):
        self.D_T_U = self.ind(self.upper_bound, self.data)
        self.Close = self.ind(self.close, self.data)
        self.D_T_L = self.ind(self.lower_bound, self.data)

    def next(self):
        if self.crossover(self.Close, self.D_T_U):
            return self.long()
        elif self.crossover(self.D_T_U, self.Close):
            return self.offset()
        elif self.crossover(self.D_T_L, self.Close):
            return self.short()


if __name__ == '__main__':
    # Prepare the data
    hb = crypto_data(name="ethusdt").loc['20220903':'20221213', ]
    yh0 = yahoo_data(name="goog").loc['20210903':'20211231', ]
    yh = yahoo_data(name="goog").loc['20210101':'20211031', ]

    # Instantiate the strategies
    MACD_run = BacktestRun(MACD(yh))
    DT_run = BacktestRun(DaulThrust(hb))
    SMA_run = BacktestRun(SMA(yh0))

    # Run and plot
    result = SMA_run.run()
    SMA_run.plot()

    result1 = MACD_run.run()
    MACD_run.plot(title="GOOG MACD Strategy")

    result2 = DT_run.run(size=10, comm=0.0003)
    DT_run.plot(title="ETHUSDT Daul-Thrust Strategy")

    # Print results
    print(result)
    print(result1)
    print(result2)

# Create your own strategies, and backtest the performance.
