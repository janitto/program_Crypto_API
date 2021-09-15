import hashlib
import hmac
import smtplib
import time
import uuid
from urllib.parse import urlencode
import requests
import json
import logging
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import base64

class Gemini:
    #   https://docs.gemini.com/rest-api/

    def __init__(self, name=""):
        self.name = name
        self.key = ""
        self.secret = ""
        self.uri = "https://api.gemini.com"

    def load_key(self, name, action):
        if name:
            with open(f"meta_login_{name}.json") as login:
                data = json.load(login)
                self.key = data[action]["api_key"]
                self.secret = data[action]["api_secret"]
                login.close()
        return

    def gemini_api_query(self, method, payload=None):
        if payload is None:
            payload = {}

        request_url = self.uri + method
        payload['request'] = method
        payload['nonce'] = int(time.time() * 1000)
        b64_payload = base64.b64encode(json.dumps(payload).encode('utf-8'))
        signature = hmac.new(self.secret.encode('utf-8'), b64_payload, hashlib.sha384).hexdigest()

        headers = {
            'Content-Type': "text/plain",
            'Content-Length': "0",
            'X-GEMINI-APIKEY': self.key,
            'X-GEMINI-PAYLOAD': b64_payload,
            'X-GEMINI-SIGNATURE': signature,
            'Cache-Control': "no-cache"
        }

        r = requests.post(request_url, headers=headers)
        return r.json()

    @staticmethod
    def get_actual_price(currency):
        pair = str(currency).lower() + "eur"
        r = requests.get(f"https://api.gemini.com/v1/pubticker/{pair}").json()
        buy = float(r['ask'])
        sell = float(r['bid'])
        return sell, buy

    def buy_limit(self, pair, eur_spend, price=False):

        """
        Args:
            pair(str)           : btceur; etheur
            eur_spend(float)    : how much money (EUR) you want to spend
            price(float)        : in case defined: make limit at defined price.
                                  In case not defined: make limit at price just below current price

        Returns:
            dict                : dictionary {} with details
        """

        self.load_key(self.name, "gemini")

        if not price:
            price = round(float(self.get_actual_price(pair[:3])[1]) * .999, 2)
        else:
            price = price
        crypto_amount = round((eur_spend * .999) / float(price), 8)
        if pair[:3] == "eth":
            crypto_amount = round(crypto_amount,6)

        payload = {
            'symbol': str(pair).upper(),
            'amount': str(crypto_amount),
            'price': str(price),
            'side': "buy",
            'options': ["maker-or-cancel"],
            'type': 'exchange limit'
        }

        # {'order_id': '40188486530', 'id': '40188486530', 'symbol': 'btceur', 'exchange': 'gemini', 'avg_execution_price': '0.00', 'side': 'buy', 'type': 'exchange limit', 'timestamp': '1621445270', 'timestampms': 1621445270483, 'is_live': True, 'is_cancelled': False, 'is_hidden': False, 'was_forced': False, 'executed_amount': '0', 'options': ['maker-or-cancel'], 'price': '33472.96', 'original_amount': '0.00014922', 'remaining_amount': '0.00014922'}

        return self.gemini_api_query("/v1/order/new", payload)

    def buy_instant(self, pair, eur_spend):
        self.load_key(self.name, "gemini")
        price = round(float(self.get_actual_price(pair[:3])[1]), 2)
        crypto_amount = round(eur_spend / float(price), 6)
        payload = {
            'symbol': str(pair).upper(),
            'amount': str(crypto_amount),
            'price': str(price),
            'side': "buy",
            'options': ["immediate-or-cancel"],
            'type': 'exchange limit'
        }

        #{'order_id': '57112684229', 'id': '57112684229', 'symbol': 'etheur', 'exchange': 'gemini', 'avg_execution_price': '2875.75', 'side': 'buy', 'type': 'exchange limit', 'timestamp': '1631275342', 'timestampms': 1631275342118, 'is_live': False, 'is_cancelled': False, 'is_hidden': False, 'was_forced': False, 'executed_amount': '0.001739', 'options': ['immediate-or-cancel'], 'price': '2875.75', 'original_amount': '0.001739', 'remaining_amount': '0'}

        return self.gemini_api_query("/v1/order/new", payload)

    def show_open_orders(self):
        self.load_key(self.name, "gemini")
        return self.gemini_api_query('/v1/orders')

    def check_status(self, order_id):
        self.load_key(self.name, "gemini")
        payload = {"order_id": order_id}
        return self.gemini_api_query("/v1/order/status", payload)

    def cancel_order(self, order_id):
        self.load_key(self.name, "gemini")

        payload = {
            "order_id": order_id
        }

        return self.gemini_api_query('/v1/order/cancel', payload)

    def get_balance(self, currency=False):
        self.load_key(self.name, "gemini")
        balance = self.gemini_api_query("/v1/balances")
        amount = float(0)
        if currency:
            for crypto in balance:
                if crypto['currency'] == str(currency).upper():
                    amount = crypto['availableForWithdrawal']
            return amount
        else:
            for crypto in balance:
                if crypto["currency"] != "EUR":
                    value = float(crypto["amount"]) * float(self.get_actual_price(f"{crypto['currency']}")[0])
                    print(f'{crypto["currency"]}: {round(float(crypto["amount"]), 8)} = {round(value, 4)} €')
                else:
                    print(f'{crypto["currency"]}: {round(float(crypto["amount"]), 4)}')
            return balance

    def get_amount_bought(self, currency, order_id):
        self.load_key(self.name, "gemini")
        payload = {'order_id': order_id}
        r = self.gemini_api_query("/v1/order/status", payload)
        if r["is_live"] is False:
            total = float(r["executed_amount"])
        else:
            total = 0
        return truncate(total)

    def withdraw_to_wallet(self, currency_to_withdraw):

        with open(f"meta_login_{self.name}.json") as login:
            data = json.load(login)
            address = data["my_addresses"][str(currency_to_withdraw).lower()]
            login.close()

        self.load_key(self.name, "gemini")
        amount = 0
        for currency in self.get_balance():
            if currency['currency'] == str(currency_to_withdraw).upper():
                amount = currency['availableForWithdrawal']
        if float(amount) != 0:
            #   to do: substract fees. (current fee is 0€)
            payload = {
                "address": address,
                "amount": amount
            }

            withdraw = self.gemini_api_query(f"/v1/withdraw/{str(currency_to_withdraw).upper()}", payload)

            # ETH
            #{'address': '0xe7af4A5d439970E30Dc6c2614838c9245bc9F680',
            # 'amount': '0.016775',
            # 'fee': '0',
            # 'withdrawalId': '60c5be6c-d2bb-4908-bcc6-1306e919b1cc',
            # 'message': 'You have requested a transfer of 0.016775 ETH to 0xe7af4A5d439970E30Dc6c2614838c9245bc9F680. This withdrawal will be sent to the blockchain within the next 60 seconds.',
            # 'txHash': 'd0e5f38b99278bf6b37ccb13a4f643a6b7ceb118f38b1537ddcc900db199cb7e'}
            # BTC
            #{'address': 'bc1qlr9lsreswkkp6plww8glhrmqwd5dc7njfy35s6',
            # 'amount': '0.0010959',
            # 'fee': '0',
            # 'withdrawalId': '60cf10bd-c392-4fb1-8b68-64a356833cd5',
            # 'message': 'You have requested a transfer of 0.0010959 BTC to bc1qlr9lsreswkkp6plww8glhrmqwd5dc7njfy35s6. This withdrawal will be sent to the blockchain within the next 60 seconds.'}

        else:
            withdraw = {"amount": "Nothing to withdraw",
                        "address": address}
        return withdraw

    def show_transactions(self, pair):
        self.load_key(self.name, "gemini")

        payload = {
            "symbol": str(pair).upper(),
            "limit_trades": 500
        }

        return self.gemini_api_query('/v1/mytrades', payload)[::-1]

    def fill_sheet_file(self, pair, sheetfile):
        crypto = str(pair[:3])
        self.load_key(self.name, "gemini")
        audit_file = authenticatespreadsheet(sheetfile, f"{self.__class__.__name__}({crypto.upper()})")
        num_rows_added = 0
        buys = self.show_transactions(pair)
        last_gemini_transaction = (list(filter(lambda x: x['Provider'] == self.__class__.__name__, audit_file.get_all_records()[-50:]))[-1]['Transaction ID'])
        for buy in buys:
            if buy['tid'] > last_gemini_transaction:
                audit_file.append_row(get_transaction_details_gemini(buy, source=self.__class__.__name__), value_input_option="USER_ENTERED")
                num_rows_added += 1
        return num_rows_added

class Kraken:

    def __init__(self, name=""):
        self.name = name
        self.key = ""
        self.secret = ""
        self.uri = "https://api.kraken.com"
        self.apiversion = "0"

    def load_key(self, name, action):
        if name:
            with open(f"meta_login_{name}.json") as login:
                data = json.load(login)
                self.key = data[action]["api_key"]
                self.secret = data[action]["api_secret"]
                login.close()
        return

    def kraken_api_query(self, method, payload=None):
        if payload is None:
            payload = {}

        request_url = f'{self.uri}/{self.apiversion}/private/{method}'

        payload['nonce'] = int(time.time() * 1000)
        postdata = urlencode(payload)
        encoded = (str(payload["nonce"]) + postdata).encode()
        message = f"/{self.apiversion}/private/{method}".encode() + hashlib.sha256(encoded).digest()
        signature = hmac.new(base64.b64decode(self.secret), message, hashlib.sha512)
        sigdigest = base64.b64encode(signature.digest())

        headers = {
            "API-Key": self.key,
            "API-Sign": sigdigest.decode()
        }

        r = requests.post(request_url, headers=headers, data=payload)
        return r.json()

    @staticmethod
    def kraken_currency_mappings(currency):

        mappings = {"btc": "xbt",
                    "doge": "xdg"}

        if currency in mappings:
            return str(mappings[currency])
        else:
            return str(currency)

    @staticmethod
    def kraken_pair_mappings(pair):
        if pair == "btceur":
            pair = "XXBTZEUR"
        if pair == "xlmeur":
            pair = "XXLMZEUR"
        if pair == "dogeeur":
            pair = "XDGEUR"
        if pair == "xrpeur":
            pair = "XXRPZEUR"
        return pair

    def get_actual_price(self, currency):
        currency_pair = str(currency).lower() + "eur"
        payload = {'pair': currency_pair.upper()}
        payload = urlencode(payload)
        try:
            price = requests.get(f"https://api.kraken.com/0/public/Ticker?{payload}").json()

            currency_pair = f"x{self.kraken_currency_mappings(currency)}zeur"
            buy = float(price["result"][currency_pair.upper()]["a"][0])
            sell = float(price["result"][currency_pair.upper()]["b"][0])
        except:
            buy = 0
            sell = 0
        return buy, sell

    def buy_limit(self, pair, eur_spend, price=False):
        self.load_key(self.name, "kraken")
        if not price:
            price = round(float(self.get_actual_price(pair[:3])[1]) * .999, 2)
        else:
            price = price
        crypto_amount = round((eur_spend * .999) / float(price), 8)

        first = self.kraken_currency_mappings(pair[:3])
        second = self.kraken_currency_mappings(pair[3:])
        pair = first + second

        payload = {"ordertype": "limit",
                   "type": "buy",
                   "volume": crypto_amount,
                   "pair": str(pair).upper(),
                   "price": float(price)
                   }

        return self.kraken_api_query("AddOrder", payload)

    def buy_instant(self, pair, eur_spend):
        self.load_key(self.name, "kraken")

        crypto_amount = round(eur_spend / self.get_actual_price(pair[:3])[1], 8)

        payload = {"ordertype": "market",
                   "type": "buy",
                   "volume": crypto_amount,
                   "pair": str(pair).upper()
                   }

        return self.kraken_api_query("AddOrder", payload)

    def show_open_orders(self):
        self.load_key(self.name, "kraken")
        return self.kraken_api_query("OpenOrders")

    def check_status(self, order_id):
        self.load_key(self.name, "kraken")
        payload = {"txid": order_id}
        return self.kraken_api_query("QueryOrders", payload)["result"][order_id]

    def cancel_order(self, order_id):
        self.load_key(self.name, "kraken")
        payload = {"txid": order_id}
        return self.kraken_api_query("CancelOrder", payload)

    def get_balance(self, currency=False):
        self.load_key(self.name, "kraken")
        r = self.kraken_api_query("Balance")
        if currency:
            mapped = self.kraken_currency_mappings(str(currency).lower)
            amount = r["result"][f"X{str(mapped).upper()}"]
            return float(amount)
        else:
            for field in r["result"]:
                if float(r["result"][field]) != 0:
                    currency = field
                    amount = r["result"][field]
                    if currency != "ZEUR":
                        value = float(amount) * self.get_actual_price(currency)[1]
                        print(f"{str(currency).upper()}: {amount} = {round(value, 4)} €")
                    else:
                        print(f"{str(currency).upper()}: {amount}")
        return r

    def get_amount_bought(self, currency, order_id):
        self.load_key(self.name, "kraken")
        payload = {"txid": order_id}
        return self.kraken_api_query("QueryOrders", payload)["result"][order_id]["vol_exec"]

    def show_transactions(self, pair):
        self.load_key(self.name, "kraken")

        pair = self.kraken_pair_mappings(pair)

        trades = []
        r = self.kraken_api_query("TradesHistory")
        for trade in r["result"]["trades"]:
            if r["result"]["trades"][trade]["pair"] == str(pair).upper():
                trades.append(r["result"]["trades"][trade])
        return trades

class Bitstamp:
    #   https://www.bitstamp.net/api/

    def __init__(self, name=""):
        self.name = name
        self.key = ""
        self.secret = b""
        self.uri = 'https://www.bitstamp.net/api'
        self.apiversion = 'v2'

    def load_key(self, name, action):
        if name:
            with open(f"meta_login_{name}.json") as login:
                data = json.load(login)
                self.key = data[action]["api_key"]
                self.secret = bytes(data[action]["api_secret"], encoding='utf-8')
                login.close()
        return

    def bitstamp_api_query(self, method, payload=None):
        timestamp, nonce, content_type = self.get_timestamp_nonce()
        if payload is None:
            string_to_sign = 'BITSTAMP ' + self.key + \
                             'POST' + \
                             'www.bitstamp.net' + \
                             f'/api/{self.apiversion}/{method}/' + \
                             '' + \
                             nonce + \
                             timestamp + \
                             self.apiversion
            string_to_sign = string_to_sign.encode('utf-8')
            signature = hmac.new(self.secret, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
            headers = {
                'X-Auth': 'BITSTAMP ' + self.key,
                'X-Auth-Signature': signature,
                'X-Auth-Nonce': nonce,
                'X-Auth-Timestamp': timestamp,
                'X-Auth-Version': self.apiversion
            }
            r = requests.post(f'{self.uri}/{self.apiversion}/{method}/', headers=headers)
        else:
            payload_string = urlencode(payload)
            string_to_sign = 'BITSTAMP ' + self.key + \
                             'POST' + \
                             'www.bitstamp.net' + \
                             f"/api/{self.apiversion}/{method}/" + \
                             '' + \
                             content_type + \
                             nonce + \
                             timestamp + \
                             self.apiversion + \
                             payload_string
            string_to_sign = string_to_sign.encode('utf-8')
            signature = hmac.new(self.secret, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
            headers = {
                'X-Auth': 'BITSTAMP ' + self.key,
                'X-Auth-Signature': signature,
                'X-Auth-Nonce': nonce,
                'X-Auth-Timestamp': timestamp,
                'X-Auth-Version': self.apiversion,
                'Content-Type': content_type
            }
            r = requests.post(f"{self.uri}/{self.apiversion}/{method}/", headers=headers, data=payload_string)
        return r.json()

    @staticmethod
    def get_timestamp_nonce():
        timestamp = str(int(round(time.time() * 1000)))
        nonce = str(uuid.uuid4())
        content_type = 'application/x-www-form-urlencoded'
        return timestamp, nonce, content_type

    @staticmethod
    def get_actual_price(currency):
        if currency != "usd":
            try:
                price = requests.get(f"https://www.bitstamp.net/api/v2/ticker/{currency}eur/")
                price = price.json()
            except:
                price = {"bid": 0, "ask": 0}
        else:
            try:
                price = requests.get(f"https://www.bitstamp.net/api/v2/ticker/eurusd/")
                price = price.json()
            except:
                price = {"bid": 0, "ask": 0}
        return float(price["bid"]), float(price["ask"])

    def buy_limit(self, pair, eur_spend, price=False):
        self.load_key(self.name, "bitstamp_buy")
        if not price:
            price = round(float(self.get_actual_price(pair[:3])[1]) * .999, 2)
        else:
            price = price
        crypto_amount = round((eur_spend * .999) / float(price), 8)

        payload = {'amount': crypto_amount, 'price': price}

        #{'price': '20000.00',
        # 'amount': '0.00104895',
        # 'type': '0',
        # 'id': '1399223761735680',
        # 'datetime': '2021-08-31 20:38:58.363000'}

        return self.bitstamp_api_query(f"buy/{pair}", payload)

    def buy_instant(self, pair, eur_spend):
        self.load_key(self.name, "bitstamp_buy")
        payload = {'amount': eur_spend}

        #{'price': '1.68678',
        # 'amount': '25.00000000',
        # 'type': '0',
        # 'id': '1337835995082753',
        # 'datetime': '2021-03-11 09:31:30.652672'}

        return self.bitstamp_api_query(f"buy/instant/{pair}", payload)

    def show_open_orders(self):
        self.load_key(self.name, "bitstamp_cancel")

        # [{'price': '0.80000',
        #   'currency_pair': 'GRT/EUR',
        #   'datetime': '2021-09-07 13:16:09',
        #   'amount': '26.22375000',
        #   'type': '0',
        #   'id': '1401592194912258'}]

        return self.bitstamp_api_query("open_orders/all")

    def check_status(self, order_id):
        self.load_key(self.name, "bitstamp_balance")
        payload = {'id': order_id}

        #{'status': 'Canceled',
        # 'id': 1401592194912258,
        # 'amount_remaining': '26.22375000',
        # 'transactions': []}

        return self.bitstamp_api_query("order_status", payload)

    def cancel_order(self, order_id):
        self.load_key(self.name, "bitstamp_cancel")
        payload = {'id': order_id}

        #{'price': 20000,
        # 'amount': 0.00104895,
        # 'type': 0,
        # 'id': 1399223761735680}


        return self.bitstamp_api_query("cancel_order", payload)

    def get_balance(self, currency=False):
        self.load_key(self.name, "bitstamp_balance")
        r = self.bitstamp_api_query("balance")
        if currency:
            amount = r[f"{currency}_available"]
            return float(amount)
        else:
            for field in r:
                if "available" in field:
                    if float(r[field]) != 0:
                        currency = str(field).split("_")[0]
                        amount = r[field]
                        if currency != "EUR":
                            value = float(amount) * self.get_actual_price(currency)[1]
                            print(f"{str(currency).upper()}: {amount} = {round(value,4)} €")
                        else:
                            print(f"{str(currency).upper()}: {amount}")
            return r

    def get_amount_bought(self, currency, order_id):
        self.load_key(self.name, "bitstamp_balance")
        payload = {'id': order_id}
        r = self.bitstamp_api_query("order_status", payload)
        if r["status"] == "Finished" or r["status"] == "Canceled":
            total = 0
            for trans in r["transactions"]:
                total+= float(trans[currency])
        else:
            total = 0
        return truncate(total)

    def withdraw_to_wallet(self, currency_to_withdraw):

        with open(f"meta_login_{self.name}.json") as login:
            data = json.load(login)
            address = data["my_addresses"][str(currency_to_withdraw).lower()]
            login.close()

        amount = self.get_balance(currency_to_withdraw)
        fee = self.get_balance()
        fee = float(fee[f"{str(currency_to_withdraw).lower()}_withdrawal_fee"])
        amount = truncate(amount-fee, decimals=6)

        if amount > 0:
            self.load_key(self.name, "bitstamp_withdraw")
            payload = {'amount': amount, 'address': address}

            #{'id': 12049423}

            return self.bitstamp_api_query(f"{str(currency_to_withdraw).lower()}_withdrawal", payload)
        else:
            return {"message": f"No {str(currency_to_withdraw).upper()} to withdraw."}

    def show_transactions(self, pair):
        self.load_key(self.name, "bitstamp_balance")
        payload = {'offset': '0', 'limit': 100, 'sort': 'asc'}
        return self.bitstamp_api_query(f"user_transactions/{pair}", payload)

    def fill_sheet_file(self, pair, sheetfile):
        crypto = str(pair[:3])
        audit_file = authenticatespreadsheet(sheetfile, f"{self.__class__.__name__}({crypto.upper()})")
        transactions = self.show_transactions(pair)
        last_bitstamp_transaction = (list(filter(lambda x: x['Provider'] == self.__class__.__name__, audit_file.get_all_records()[-50:]))[-1]['Transaction ID'])
        num_rows_added = 0
        for transaction in transactions:
            if transaction['id'] > last_bitstamp_transaction:
                audit_file.append_row(get_transaction_details_bitstamp(transaction, crypto, source=self.__class__.__name__), value_input_option="USER_ENTERED")
                num_rows_added += 1
                time.sleep(0.5)
        return num_rows_added
#---------------------------
    def sell_limit(self, pair, amount, price):
        self.load_key(self.name, "bitstamp_sell")
        timestamp, nonce, content_type = self.get_timestamp_nonce()
        payload = {'amount': amount, 'price': price}
        payload_string = urlencode(payload)
        string_to_sign = 'BITSTAMP ' + self.key + \
                         'POST' + \
                         'www.bitstamp.net' + \
                         f"/api/{self.apiversion}/sell/{pair}/" + \
                         '' + \
                         content_type + \
                         nonce + \
                         timestamp + \
                         self.apiversion + \
                         payload_string
        string_to_sign = string_to_sign.encode('utf-8')
        signature = hmac.new(self.secret, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
        headers = {
            'X-Auth': 'BITSTAMP ' + self.key,
            'X-Auth-Signature': signature,
            'X-Auth-Nonce': nonce,
            'X-Auth-Timestamp': timestamp,
            'X-Auth-Version': self.apiversion,
            'Content-Type': content_type
        }
        r = requests.post(f"{self.uri}/{self.apiversion}/sell/{pair}/", headers=headers, data=payload_string)
        # {'price': '1.72000', 'amount': '14.82113850', 'type': '1', 'id': '1337840616333312', 'datetime': '2021-03-11 09:50:18.892807'}
        return r.json()

    def sell_trailing(self, currency, amount, trailing_percent):
        active_sell_price, _ = self.get_actual_price(currency)
        trailing_value = round(active_sell_price * trailing_percent, 3)
        logging.info(f"Zacinam trailing sell pri cene {active_sell_price}. Trailing {trailing_value}")
        time.sleep(60)
        while True:
            sell_price, _ = self.get_actual_price(currency)
            if sell_price > active_sell_price:
                active_sell_price = sell_price
                logging.info(f"Limit na trailing sell sa zvysil na {round(active_sell_price - trailing_value, 3)}")
                time.sleep(60)
            elif sell_price < active_sell_price - trailing_value:
                logging.debug(f"Cena {sell_price} je nizsia ako {round(active_sell_price - trailing_value,3)}. Predavam.")
                r = self.sell_instant(currency+"eur", amount)
                prijem = float(r["amount"])*active_sell_price
                logging.info(f"Trailing ukonceny. Prijem pri kurze {active_sell_price} je {prijem}")
                break
            else:
                logging.debug(f"Trailing sell stale aktivny. Sell pri {round(active_sell_price - trailing_value, 3)}, teraz {active_sell_price}")
                time.sleep(60)
        return r

    def sell_instant(self, pair, amount):
        self.load_key(self.name, "bitstamp_sell")
        timestamp, nonce, content_type = self.get_timestamp_nonce()
        payload = {'amount': amount}
        payload_string = urlencode(payload)
        string_to_sign = 'BITSTAMP ' + self.key + \
                         'POST' + \
                         'www.bitstamp.net' + \
                         f"/api/{self.apiversion}/sell/instant/{pair}/" + \
                         '' + \
                         content_type + \
                         nonce + \
                         timestamp + \
                         self.apiversion + \
                         payload_string
        string_to_sign = string_to_sign.encode('utf-8')
        signature = hmac.new(self.secret, msg=string_to_sign, digestmod=hashlib.sha256).hexdigest()
        headers = {
            'X-Auth': 'BITSTAMP ' + self.key,
            'X-Auth-Signature': signature,
            'X-Auth-Nonce': nonce,
            'X-Auth-Timestamp': timestamp,
            'X-Auth-Version': self.apiversion,
            'Content-Type': content_type
        }
        r = requests.post(f"{self.uri}/{self.apiversion}/sell/instant/{pair}/", headers=headers, data=payload_string)
        return r.json()


def send_mail(crypto, price, action, body):

    with open(f"trading_bots/meta_login_example.json") as login:
        data = json.load(login)
        gmail_username = data["gmail"]["email"]
        gmail_password = data["gmail"]["password"]
        login.close()

    try:
        server = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        server.ehlo()
        server.login(gmail_username, gmail_password)
        server.sendmail(gmail_username, gmail_username,
                        f"Subject: {crypto.upper()} was {action} at price {price}\n\n{body}")
        server.quit()
        print("Email sent successfully.")
    except:
        print('Something went wrong with email sending...')

def truncate(n, decimals=8):
    multiplier = 10 ** decimals
    return int(n * multiplier) / multiplier

def authenticatespreadsheet(doc_name, sheet_name):
    # obtain JSON file from https://console.cloud.google.com/ - video: https://www.youtube.com/watch?v=V51zRxLAVWU&t=646s
    scope = ["https://spreadsheets.google.com/feeds",
             'https://www.googleapis.com/auth/spreadsheets',
             "https://www.googleapis.com/auth/drive.file",
             "https://www.googleapis.com/auth/drive"]
    creds = ServiceAccountCredentials.from_json_keyfile_name("google_cheets.json", scope)
    client = gspread.authorize(creds)
    return client.open(doc_name).worksheet(sheet_name)

def get_transaction_details_gemini(transaction, source):
    transaction_date = str(datetime.fromtimestamp(transaction['timestamp']).date())
    transaction_id = float(transaction['tid'])
    provider = source
    quantity = float(transaction['amount'])
    btc_price = float(transaction['price'])
    fee = float(transaction['fee_amount'])
    transaction_type = transaction["type"]
    eur_amount = quantity * btc_price + fee
    return [transaction_date, transaction_id, provider, transaction_type, quantity, btc_price, eur_amount, fee]

def get_transaction_details_bitstamp(transaction, crypto, source):
    datum = transaction["datetime"]
    datum = datetime.strptime(datum, '%Y-%m-%d %H:%M:%S.%f')
    transaction_date = datum.strftime("%Y-%m-%d")
    transaction_id = float(transaction['id'])
    provider = source
    quantity = float(transaction[crypto])
    btc_price = float(transaction[f'{crypto}_eur'])
    fee = float(transaction['fee'])
    if float(transaction[crypto]) < 0:
        transaction_type = "Sell"
    else:
        transaction_type = "Buy"
    eur_amount = quantity * btc_price + fee
    return [transaction_date, transaction_id, provider, transaction_type, abs(quantity), btc_price, abs(eur_amount), fee]
