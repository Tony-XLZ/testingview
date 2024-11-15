from testingview import StrategyBase, BacktestRun
from testingview import yahoo_data

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


if __name__ == '__main__':
    # Prepare the data
    yh = yahoo_data(name="goog").loc['20210903':'20211231', ]

    # Instantiate the strategies
    SMA_run = BacktestRun(SMA(yh))

    # Run and plot
    result = SMA_run.run()
    SMA_run.plot()

    # Print results
    print(result)

# Create your own strategies, and backtest the performance.
