from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort

import json
import sqlite3
import markdown2 as markdown
from pygments.formatters import HtmlFormatter



from bin.exchanges import Gemini, Kraken, Bitstamp

bitstamp = Bitstamp("jany")
gemini = Gemini("jany")
kraken = Kraken("jany")


app = Flask(__name__)
api = Api(app)

balance_get_args = reqparse.RequestParser()
balance_get_args.add_argument('currency')

transastions_get_args = reqparse.RequestParser()
transastions_get_args.add_argument("since")

defined_exchanges = ["gemini", "bitstamp", "kraken"]

def abort_if_invalid_exchange(exchange):
    if exchange not in defined_exchanges:
        abort(404, message="Exchange " + exchange + " not included in project. Use Gemini, Kraken or Bitstamp")

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
    cursor.execute("select count(*) from trades")
    number_of_lines = cursor.fetchall()[0][0]
    if number_of_lines == 0:
        db_status = "EMPTY"
    else:
        db_status = f"{number_of_lines} wors"

    return {"SERVER status": "UP",
            "DB status": db_status}, 200

@app.route("/balance/<exchange>")
def get_balance(exchange):
    abort_if_invalid_exchange(str(exchange).lower())
    args = balance_get_args.parse_args()

    if args["currency"] is not None:
        currency = args["currency"]
    else:
        currency = ""

    if exchange == "gemini":
        balance = gemini.get_balance(currency)
    elif exchange == "kraken":
        balance = kraken.get_balance(currency)
    else:
        balance = bitstamp.get_balance(currency)

    return {'exchange': exchange,
            "currency": currency,
            "balance": balance}, 200

@app.route("/audit/<exchange>/<currency>")
def audit(exchange, currency):
    return eval(f"{exchange}.draw_chart(\"{currency.upper()}\")")

@app.route("/transactions/<exchange>/<pair>")
def get(exchange, pair):
    abort_if_invalid_exchange(str(exchange).lower())
    args = transastions_get_args.parse_args()

    if exchange == "gemini":
        transactions = gemini.show_transactions(pair)
        if args["since"] is not None:
            valid_transactions = []
            from datetime import datetime as dt
            for transaction in transactions:
                if transaction["timestamp"] > dt.strptime(args["since"], "%d-%m-%Y").timestamp():
                    valid_transactions.append(transaction)
            return json.dumps(valid_transactions), 200
        return json.dumps(transactions), 200
    elif exchange == "kraken":
        transactions = kraken.show_transactions(pair)
        if args["since"] is not None:
            valid_transactions = []
            from datetime import datetime as dt
            for transaction in transactions:
                if transaction["time"] > dt.strptime(args["since"], "%d-%m-%Y").timestamp():
                    valid_transactions.append(transaction)
            return json.dumps(valid_transactions), 200
        return json.dumps(transactions), 200
    else:
        transactions = bitstamp.show_transactions(pair)
        if args["since"] is not None:
            valid_transactions = []
            from datetime import datetime as dt
            for transaction in transactions:
                if dt.strptime(transaction["datetime"], "%Y-%m-%d %H:%M:%S.%f") > dt.strptime(args["since"], "%d-%m-%Y"):
                    valid_transactions.append(transaction)
            return json.dumps(valid_transactions), 200
        return json.dumps(transactions), 200


app.run(port=1521, host="0.0.0.0")