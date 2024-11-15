# README: Python for Finance - Backtesting Framework "testingview"

## Introduction

"testingview" is a lightweight, event-driven backtesting framework built with object-oriented programming for quantitative finance. It enables users to evaluate the profitability of various trading strategies by simulating their performance over historical data. The framework provides an effective way to test strategies in a wide range of market conditions, recognizing that while past performance is not a guarantee of future results, well-tested strategies can offer valuable insights.

The report is divided into two parts:
1. **Documentation**: Detailed guidance on usage, framework objects, and maintenance.
2. **Reflective Account**: Reflections on the development process, challenges encountered, and lessons learned.
3. **Appendix**: Install commands for required packages are included in the appendix.

## Quickstart Example

```python
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
    yh = yahoo_data(name="goog").loc['20210903':'20211231']

    # Instantiate the strategy
    SMA_run = BacktestRun(SMA(yh))

    # Run and plot
    result = SMA_run.run()
    SMA_run.plot()

    # Print results
    print(result)
```

To run a backtest using "testingview":
1. Prepare the data.
2. Create a strategy by inheriting from `StrategyBase`.
3. Run the backtest using `BacktestRun`.
4. Print and plot the results.

The "simple_example.py" shows how a simple moving average (SMA) strategy is run on "GOOG" data from September 3, 2021, to December 31, 2021. By overriding two abstract methods (`set_indicators()` and `next()`), you can define your own trading strategy.

The framework runs by default with $50,000 starting capital, 0% broker commission, and 100 shares of Alphabet Inc. (GOOG) traded. During the selected period, the strategy incurred a 3.79% loss.

## Reference Documentation

"testingview" consists of three submodules:
1. **testingview.strategybase**: Core framework structure for building strategies.
2. **testingview.strategyrun**: Structure for backtesting analysis and visualization.
3. **testingview.datafeeds**: Data from Huobi and Yahoo Finance APIs, cleaned and prepared for use.

### Module Details

**testingview.strategybase**
- `class StrategyBase(data)`: The abstract base class to define trading strategies.
  - **Methods**:
    - `set_indicators()`: Override to create strategy indicators.
    - `next()`: The main strategy method to define trade signals.
    - `long()`, `short()`, `offset()`: Place long, short, or offset positions.
    - `crossover()`: Check if one series crosses over another.

**testingview.strategyrun**
- `class BacktestRun(strategy)`: Backtest a `StrategyBase` subclass.
  - **Methods**:
    - `run(cash=50000, size=100, comm=0, amount=1)`: Run the backtest with specified parameters.
    - `plot(title=None, type='candle')`: Plot results.

**testingview.datafeeds**
- `crypto_data(name='btcusdt')`: Load Huobi data for specified currency pairs.
- `yahoo_data(name='aapl')`: Load Yahoo Finance data for specified stocks.

## Advanced Tutorials

### MACD Example

```python
from testingview import StrategyBase, BacktestRun
def yahoo_data
import numpy as np

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

    def set_indicators(self):
        self.MACD = self.ind(self.macd, self.data.close)
        self.MACDsignal = self.ind(self.macd_s, self.data.close)

    def next(self):
        if self.crossover(self.MACD, self.MACDsignal):
            return self.long()
        elif self.crossover(self.MACDsignal, self.MACD):
            return self.short()

if __name__ == '__main__':
    # Prepare the data
    yh = yahoo_data(name="goog").loc['20210101':'20211231']

    # Instantiate the strategy
    MACD_run = BacktestRun(MACD(yh))

    # Run and plot
    result = MACD_run.run()
    MACD_run.plot(title="GOOG MACD Strategy")

    # Print results
    print(result)
```

The logic is straightforward: go long when MACD crosses above the signal line, and go short when it crosses below.

### Dual Thrust Strategy Example

```python
from testingview import StrategyBase, BacktestRun
from testingview import crypto_data
import numpy as np

class DualThrust(StrategyBase):
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
        return _df.open - 0.3 * np.maximum(hh - lc, hc - ll)

    def set_indicators(self):
        self.D_T_U = self.ind(self.upper_bound, self.data)
        self.D_T_L = self.ind(self.lower_bound, self.data)
        self.Close = self.ind(lambda x: x.close, self.data)

    def next(self):
        if self.crossover(self.Close, self.D_T_U):
            return self.long()
        elif self.crossover(self.D_T_U, self.Close):
            return self.offset()
        elif self.crossover(self.D_T_L, self.Close):
            return self.short()

if __name__ == '__main__':
    # Prepare the data
    hb = crypto_data(name="ethusdt").loc['20220903':'20221213']

    # Instantiate the strategy
    DT_run = BacktestRun(DualThrust(hb))

    # Run and plot
    result = DT_run.run(cash=500000, size=10, comm=0.0003, amount=1)
    DT_run.plot(title="ETHUSDT Dual-Thrust Strategy")

    # Print results
    print(result)
```

The Dual Thrust strategy uses upper and lower bounds calculated from recent price movements to determine entry and exit points. The strategy goes long when the closing price crosses above the upper bound, offsets the position when the price crosses back below, and goes short when the price crosses below the lower bound.

## Reflective Account

Building "testingview" was a challenging and rewarding experience. It pushed me beyond my comfort zone and required me to apply both programming and finance skills extensively. Debugging was particularly time-consuming, which taught me the importance of planning and unit testing to avoid major setbacks later in the development process. The project also helped me appreciate the flexibility of Python and the power of object-oriented programming.

## Appendix: Install Commands for Required Packages
```
conda install numpy
conda install pandas
conda install matplotlib
conda install -c conda-forge ta-lib
pip install mplfinance
pip install yfinance
```

