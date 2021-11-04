from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort

import markdown2 as markdown
from pygments.formatters import HtmlFormatter



from exchanges import Gemini, Kraken, Bitstamp

bitstamp = Bitstamp("example")
gemini = Gemini("example")
kraken = Kraken("example")


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
def get():
    with open("README.md", "r") as markdown_file:
        formatter = HtmlFormatter(style="emacs", full=True, cssclass="codehilite")
        css_string = formatter.get_style_defs()
        md_css_string = "<style>" + css_string + "</style>"
        md_template = md_css_string + markdown.markdown(markdown_file.read(), extras=['fenced-code-blocks', "tables"])
        return md_template

class HealthCheck(Resource):

    @staticmethod
    def get():
        return {"status": "UP"}, 200

class ShowBalance(Resource):
    @staticmethod
    def get(exchange):
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

class ShowTransactions(Resource):
    @staticmethod
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
                return valid_transactions
        elif exchange == "kraken":
            transactions = kraken.show_transactions(pair)
            if args["since"] is not None:
                valid_transactions = []
                from datetime import datetime as dt
                for transaction in transactions:
                    if transaction["time"] > dt.strptime(args["since"], "%d-%m-%Y").timestamp():
                        valid_transactions.append(transaction)
                return valid_transactions
        else:
            transactions = bitstamp.show_transactions(pair)
            if args["since"] is not None:
                valid_transactions = []
                from datetime import datetime as dt
                for transaction in transactions:
                    if dt.strptime(transaction["datetime"], "%Y-%m-%d %H:%M:%S.%f") > dt.strptime(args["since"], "%d-%m-%Y"):
                        valid_transactions.append(transaction)
                return valid_transactions
        return transactions, 200

api.add_resource(HealthCheck, "/healthcheck")
api.add_resource(ShowBalance, '/balance/<exchange>')
api.add_resource(ShowTransactions, '/transactions/<exchange>/<pair>')


app.run(port=7777, host="0.0.0.0")