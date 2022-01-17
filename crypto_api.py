import pandas as pd
from flask import Flask
from flask_restful import Api, reqparse

import requests
import time
import sqlite3
import markdown2 as markdown
from pygments.formatters import HtmlFormatter
import altair as alt
import datetime


from bin.exchanges import Gemini, Kraken, Bitstamp

app = Flask(__name__)
api = Api(app)

balance_get_args = reqparse.RequestParser()
balance_get_args.add_argument('user')
balance_get_args.add_argument('currency')

defined_exchanges = ["gemini", "bitstamp", "kraken"]


@app.route("/")
def index():
    with open("README.md", "r") as markdown_file:
        formatter = HtmlFormatter(style="emacs", full=True, cssclass="codehilite")
        css_string = formatter.get_style_defs()
        md_css_string = "<style>" + css_string + "</style>"
        md_template = md_css_string + markdown.markdown(markdown_file.read(), extras=['fenced-code-blocks', "tables"])
        return md_template


@app.route("/healthcheck")
def healthcheck():

    conn = sqlite3.connect("bin/trades.db", check_same_thread=False)
    cursor = conn.cursor()
    try:
        cursor.execute("select count(*) from trades")
        number_of_lines = cursor.fetchall()[0][0]
    except:
        number_of_lines = 0
    if number_of_lines == 0:
        db_status = "EMPTY"
    else:
        db_status = f"{number_of_lines} rows"

    return {"SERVER status": "UP",
            "DB status": db_status}, 200

@app.route("/balance")
def help_balance():
    return "Correct usage is: /balance/user/exchange?currency=btc", 200

@app.route("/balance/<user>/<exchange>")
# .../exchange?currency=btc
def get_balance(user, exchange):
    args = balance_get_args.parse_args()

    if args["currency"] is not None:
        currency = args["currency"]
    else:
        currency = False

    if exchange.lower() == "bitstamp":
        balance = Bitstamp(name=user).get_balance(currency)
    elif exchange.lower() == "kraken":
        balance = Kraken(name=user).get_balance(currency)
    elif exchange.lower() == "gemini":
        balance = Gemini(name=user).get_balance(currency)
    else:
        return "Unknown exchange defined.", 401

    return {'exchange': exchange,
            "currency": currency,
            "balance": balance}, 200

@app.route("/audit")
def help_audit():
    return "Correct usage is: /audit/user/exchange/currency", 200

@app.route("/audit/<user>/<exchange>/<currency>")
def audit(user, exchange, currency):
    if exchange.lower() == "bitstamp":
        return Bitstamp(name=user).draw_chart(currency.upper()), 200
    elif exchange.lower() == "kraken":
        return Kraken(name=user).draw_chart(currency.upper()), 200
    elif exchange.lower() == "gemini":
        return Gemini(name=user).draw_chart(currency.upper()), 200
    else:
        return "Something went wrong. Check: /audit/<user>/<exchange>/<currency>", 401

@app.route("/trades_over_time")
def help_trades_over_time():
    return "Correct usage is: /trades_over_time/user/exchange/currency", 200

@app.route("/trades_over_time/<user>/<exchange>/<currency>")
def trades_over_time(user, exchange, currency):

    # get candles from binance
    params = {"symbol": f"{currency.upper()}EUR",
              "interval": "1d",
              "startTime": int(time.time() * 1000) - 31536000000,
              "endTime": int(time.time() * 1000)}
    r = requests.get("https://api.binance.com/api/v3/klines", params=params)

    candles = pd.DataFrame(columns=["Date", "Open", "High", "Low", "Close", "Trade"])
    for x in r.json():
        candles = candles.append({"Date": datetime.datetime.fromtimestamp(x[0]/1000.0).strftime("%Y-%m-%d"),
                                  "Open": x[1],
                                  "High": x[2],
                                  "Low": x[3],
                                  "Close": x[4],
                                  "Trade": False}, ignore_index=True)

    # add trades
    trades = pd.read_sql_query(f"select * from trades "
                               f"where provider = \"{str(exchange).capitalize()}\" "
                               f"and currency = \"{currency.upper()}\" "
                               f"and user = \"{user}\" "
                               f"order by date desc", sqlite3.connect("bin/trades.db", check_same_thread=False))

    connected = candles.merge(trades, how="left", left_on="Date", right_on="date")

    # create candlechart
    base = alt.Chart(connected).encode(
        alt.X('Date:T',
              axis=alt.Axis(
                  format='%d.%m.%y',
                  labelAngle=-45)
              )
    ).properties(width=1100, height=500)

    rule = base.mark_rule(color="lightgray").encode(
        alt.Y(
            'Low:Q',
            title='Price',
            scale=alt.Scale(zero=False),
        ),
        alt.Y2('High:Q')
    )

    bar = base.mark_bar(color="lightgray").encode(
        alt.Y('Open:Q'),
        alt.Y2('Close:Q')
    )

    domain = ['Buy', 'Sell']
    range = ['red', 'green']

    dots = base.mark_circle(size=50, opacity=1).encode(
        alt.X('Date:T'),
        alt.Y('price:Q'),
        color = alt.Color('type',scale=alt.Scale(domain=domain, range=range)),
        tooltip=['Date',
                 'internal_id', 'type', 'quantity', 'price', 'eur_spent',
                 'fee']
    )
    curr_price = requests.get(f"https://api.binance.com/api/v3/ticker/price?symbol={currency.upper()}EUR")
    curr_price = pd.DataFrame(curr_price.json(), columns=["symbol", "price"], index=[1])

    line = alt.Chart(curr_price).mark_rule(color='green', opacity=1).encode(
        alt.Y('price:Q')
    )

    (rule + bar + dots + line).save('tmp/chart.html')
    with open("tmp/chart.html", "r") as f:
        html = f.read()
    return html


app.run(port=1521, host="0.0.0.0")
