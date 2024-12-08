from numbers import Number
from .strategybase import StrategyBase

import warnings
import numpy as np
import pandas as pd
import matplotlib.dates as mdate
import mplfinance as mpf


class BacktestRun:
    """
    Backtest a particular strategy on the data
    provided in 'strategybase.StrategyBase'.

    Upon initialization, receive siglist from
    'strategybase.StrategyBase',and call method
    'strategyrun.BacktestRun.run' to run a backtest
    with broker statistics settled.

    Receives strategy which is a StrategyBase subclass.
    """

    def __init__(self, strategy):
        # Debug the 'strategy' type
        if not issubclass(type(strategy), StrategyBase):
            raise TypeError("'strategy' must be a StrategyBase subtype")

        self._data = strategy.data
        self._indicators = strategy._indicators
        self._strategy = strategy
        self._result = None

    def _broker(self):  # I.
        # Core method to generate the statistics of the strategy backtesting
        self._data['change'] = self._data.close.diff()
        self._data['signal'] = self._strategy._sig()
        for df in self._indicators:
            self._data[df.columns] = df
        self._data['pos'] = self._data.signal.fillna(method='ffill').shift().fillna(0)
        self._data['trading_pnl'] = self._data.change * self._data.pos * self.size
        self._data['fee'] = self._data.close * self.size * self.amount * self.comm * \
                            abs(self._data['pos'] - self._data['pos'].shift()).fillna(0)
        self._data['netpnl'] = self._data['trading_pnl'] - self._data['fee']
        self._data.netpnl.fillna(0, inplace=True)
        self._data['cumpnl'] = self._data['netpnl'].cumsum()
        self._data['capital'] = self._data['cumpnl'] + self.cash
        self._data['outofmoney'] = \
            (self._data.capital.shift() <= self._data.close * self.size * self.amount + self._data.fee) \
            & (self._data.fee != 0)

    def run(self, cash=50000, size=100, comm=0, amount=1):  # I.
        """
        Run the backtest. Returns 'pd.Series' with results.
        Accept Number objects 'cash', 'size', 'comm', and 'amount'.

        'cash' is the start cash of the process, default is 50000 unit
        'size' is total the number of shares traded within one trading process(i.e., 'long', 'short' or 'offset')
        'comm' is broker's commission, default is 0
        'amount' is the number of transactions within one trading process, default is 1
        """
        # Check if the value input is Number objects
        if not all(isinstance(i, Number) for i in [cash, size, comm, amount]):
            raise TypeError("'cash', 'size', 'comm' and 'amount' must be Number")
        self.cash = cash
        self.size = size
        self.comm = comm
        self.amount = amount

        # Run 'self._broker()'
        self._broker()

        # Create pd.Series to show the result
        r = pd.Series(dtype=object)
        r.loc['Strategy name'] = type(self._strategy).__name__
        r.loc['Valid or not'] = sum(self._data.outofmoney) == 0
        r.loc['(Not valid means'] = '(Increase cash value'
        r.loc['out of money)'] = 'if False)'
        r.loc['Start'] = self._data.index[0]
        r.loc['End'] = self._data.index[-1]
        r.loc['Duration'] = r.End - r.Start
        r.loc['Exposure Time %'] = ((r.Duration.days - len(self._data[self._data.pos == 0])) / r.Duration.days) * 100
        r.loc['Capital Final $'] = self._data.capital[-1]
        r.loc['Capital Peak $'] = self._data.capital.max()
        r.loc['Return %'] = (self._data.capital[-1] - self._data.capital[0]) / self._data.capital[0] * 100
        dd = 1 - self._data.capital / np.maximum.accumulate(self._data.capital)
        r.loc['Max Drawdown %'] = -np.nan_to_num(dd.max()) * 100
        self._result = r
        pd.option_context('max_colwidth', 20)
        return r

    def plot(self, title=None, type='candle'):  # I. and II.
        """
        Plot the backtest with financial statistics and portfolio value.
        Accepts 'title' as string, default is the name of the class created.
        Accepts 'type' as string from
        'line', 'ohlc' and 'candle', default is 'candle'.
        """
        # Generate plot title
        if title is None:
            if self._result is not None:
                title = self._result[0]
            else:
                title = 'Backtesting Plot'
        else:
            try:
                title = str(title)
            except Exception:
                raise TypeError("title should be a string")

        # Check the 'type' argument
        if type not in ('line', 'ohlc', 'candle'):
            raise ValueError("'type' must be string from "
                             "'line', 'ohlc' and 'candle'(Case sensitive)")
        pldata = self._data

        # We can only plot after running the strategy
        try:
            pldata['signal1'] = pldata[pldata.signal == 1].signal * pldata.close
        except AttributeError:
            raise _PlotBeforeRun('run() have to be executed before plot()')

        pldata['signal0'] = (pldata[pldata.signal == 0].signal + 1) * pldata.close
        pldata['signal-1'] = -pldata[pldata.signal == -1].signal * pldata.close

        # Set mpl-plot color
        my_color = mpf.make_marketcolors(up='SeaGreen',
                                         down='r',
                                         edge='inherit',
                                         wick='inherit',
                                         volume='inherit')

        # Set background color
        my_style = mpf.make_mpf_style(marketcolors=my_color,
                                      figcolor='(0.82, 0.83, 0.85)',
                                      gridcolor='(0.82, 0.83, 0.85)')

        # Create a dict() of signal plots to add
        ap = dict()
        if sum(pldata['signal1'].isnull()) != len(pldata['signal1']):
            ap['long'] = (mpf.make_addplot(pldata['signal1'], type='scatter', markersize=80, marker='^', color='g'))
        if sum(pldata['signal-1'].isnull()) != len(pldata['signal-1']):
            ap['short'] = (mpf.make_addplot(pldata['signal-1'], type='scatter', markersize=80, marker='v', color='r'))
        if sum(pldata['signal0'].isnull()) != len(pldata['signal0']):
            ap['offset'] = (mpf.make_addplot(pldata['signal0'], type='scatter', markersize=80, marker='o', color='y'))

        # Create figures and axes derived from mplfinance
        fig, ax = mpf.plot(pldata, addplot=list(ap.values()), type=f'{type}',
                           volume=True, style=my_style, figsize=(12, 8), returnfig=True)

        # Set the position of axes
        ax[0].set_position([0.1, 0.50, 0.88, 0.40])
        ax[2].set_position([0.1, 0.40, 0.88, 0.10])
        ax2 = fig.add_axes([0.1, 0.2, 0.88, 0.20])
        ax3 = fig.add_axes([0.1, 0.05, 0.88, 0.15], sharex=ax2)

        # Set ax3 ylabel
        ax3.set_ylabel('Portfolio Value')

        # Hide the ax2 tick
        for tick in ax2.get_xticklabels():
            tick.set_rotation(90)

        # Set ax2 ylabel and tick format
        ax2.set_ylabel('Indicators')
        ax2.xaxis.set_major_formatter(mdate.DateFormatter('%Y-%m-%d'))

        # Hide x grids since it cannot be aligned
        ax2.grid(which='major', axis='x')
        ax3.grid(which='major', axis='x')
        ax[0].grid(which='major', axis='x')
        ax[2].grid(which='major', axis='x')

        # Create plot title
        title_font = {'fontname': 'Arial',
                      'size': '30',
                      'color': 'black',
                      'weight': 'bold',
                      'va': 'bottom',
                      'ha': 'center'}
        fig.text(0.50, 0.92, f'{title}', **title_font)

        # Plot indicators and portfolio value
        ax2.plot(pldata[[list(df)[0] for df in self._indicators]], label=[list(df)[0] for df in self._indicators])
        ax3.plot(pldata['capital'], label='capital')

        # Create legends
        ax2.legend()
        ax3.legend()

        # II. Module 'mplfinance' does not support legends, so I refer to the answer here and made some adjustments.
        # https://github.com/matplotlib/mplfinance/issues/181#issuecomment-1068141054
        # Here we create legends for 'long', 'short' and 'offset'.
        ax[0].legend([None] * (len(ap) + 2))
        handles = ax[0].get_legend().legend_handles
        ax[0].legend(handles=handles[2:], labels=list(ap.keys()))

        # Show the plot
        warnings.filterwarnings("ignore", module="matplotlib\..*")
        fig.show()


class _PlotBeforeRun(Exception):
    pass


# P.S.:
# I. My work and entirely original code
# II. Based on an existing source which has then been adapted to some degree
# III. Entirely copied from an existing source
