import pandas as pd
import plotly.graph_objects as go
import mplfinance as mpf
import numpy as np
import requests

r = requests.get("https://api.gemini.com/v2/candles/btceur/1day")
btc_prices = pd.DataFrame(r.json(), columns =['Time','Open','High','Low','Close','Volume'])

btc_prices['Time'] = pd.to_datetime(btc_prices['Time'], unit='ms')
btc_prices.set_index('Time', inplace=True)
btc_prices.sort_values(by =['Time'], inplace = True)

btc_prices["long_trend"] = btc_prices["Close"].rolling(window=30, min_periods=1).mean()
btc_prices["short_trend"] = btc_prices["Close"].rolling(window=7, min_periods=1).mean()

btc_prices['Strategy'] = np.where(btc_prices['long_trend'] > btc_prices['short_trend'], "Buy", "")

#mpf.plot(btc_prices, type='candle', mav=50, volume=True)

candlestick = go.Candlestick(
    x=btc_prices.index,
    open=btc_prices['Open'],
    high=btc_prices['High'],
    low=btc_prices['Low'],
    close=btc_prices['Close'],
    showlegend=False
)

long_trend = go.Scatter(
    x=btc_prices.index,
    y=btc_prices["long_trend"],
    name="Long-trend"
)

short_trend = go.Scatter(
    x=btc_prices.index,
    y=btc_prices["short_trend"],
    name="Short-trend"
)

fig = go.Figure(data=[candlestick, long_trend, short_trend])

fig.update_layout(
    title="Past year trades.",
    yaxis_title='Price',
    xaxis_rangeslider_visible=False,

)

print(btc_prices)

fig.show()