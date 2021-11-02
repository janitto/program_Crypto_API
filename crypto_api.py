from flask import Flask, request
from flask_restful import Resource, Api, reqparse, abort

from exchanges import Gemini, Kraken, Bitstamp

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


class Balance(Resource):
    def get(self, exchange):
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
    def get(self, exchange, pair):
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
        else:
            transactions = bitstamp.show_transactions(pair)

        return transactions, 200

api.add_resource(Balance, '/balance/<exchange>')
api.add_resource(ShowTransactions, '/transactions/<exchange>/<pair>')


app.run(port=7777, host="0.0.0.0")