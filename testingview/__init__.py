# As a student majored in finance, I am always
# interested in the financial markets, i.e., derivative market,
# stock market, and crypto market. We have tons of trading strategies.
# But how to know if a strategy is truly profitable?
# I think the best way is to run it in the history.
# Of course, past performance cannot indicate
# future results directly, but a strategy that has proven
# itself effective in a wide range of market conditions can,
# to some extent, be just as reliable in the future.
# So, I built a lightweight, event-driven back-testing framework
# “testingview” with object-oriented programming for quantitative finance.

from .strategyrun import BacktestRun
from .strategybase import StrategyBase
from .datafeeds import *
