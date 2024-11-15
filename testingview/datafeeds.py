# This module is totally type I.

import pandas as pd
import time as _time
import requests

import yfinance as yf


def crypto_data(name="btcusdt"):
    """
    Return Dataframed daily data from Huobi API
    Receives 'name' to choose the currency,
    i.e., 'ethusdt', 'ltcusdt', ...
    default 'name' is 'btcusdt'
    """

    # Prepare the url
    MARKET_URL = "https://api.huobi.pro"

    symbol = name
    period = "1day"
    size = "2000"

    url = MARKET_URL + '/market/history/kline?' + 'period=' + period + '&size=' + size + '&symbol=' + symbol

    # Get responds
    resp = requests.get(url)

    resp_json = resp.json()
    data_list = resp_json['data']

    # Prepare data
    df = pd.DataFrame(data_list)
    df['date'] = pd.to_datetime(df['id'], unit='s')
    df.index = df['date']
    df = df.rename(columns={'vol': 'volume'})

    return df[['open', 'close', 'high', 'low', 'volume']][::-1]

def yahoo_data(name="aapl"):
    """
    Return Dataframed daily data from Yahoo Finance.
    Receives 'name' to choose the stock,
    i.e., 'goog', 'msft', ...
    default 'name' is 'aapl'
    """

    # Create the ticker
    tick = yf.Ticker(name)

    # Prepare data
    tick_historical = tick.history(start="1900-01-01", end=int(_time.time()), interval="1d")
    tick_historical.columns = tick_historical.columns.map(lambda x:x. lower())

    return tick_historical[['open', 'close', 'high', 'low', 'volume']]


# P.S.:
# I. My work and entirely original code
# II. Based on an existing source which has then been adapted to some degree
# III. Entirely copied from an existing source
