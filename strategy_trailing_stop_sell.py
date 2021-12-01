#!/usr/bin/env python3

from bin.exchanges import Gemini, Bitstamp, Kraken
import argparse
import logging
from time import sleep


parser = argparse.ArgumentParser()
parser.add_argument('currency', type=str, help="Possible crypto: btc/eth/...")
parser.add_argument('amount', type=float, help="Amount to sell")
parser.add_argument('trailing', type=float, help="Value for trailing stop in %")
args = parser.parse_args()
currency = args.crypto
amount = args.amount
trailing = args.trailing


logging.basicConfig(filename="logs/TS_logfile.log",
                    filemode="a",
                    format="%(asctime)s - %(message)s",
                    level="INFO")

exchange = Gemini("example")
#exchange = Bitstamp("example")
#exchange = Kraken("example")

active_sell_price, _ = exchange.get_actual_price(currency)
trailing_value = round(active_sell_price * trailing / 100, 3)
logging.info(f"Trailing limit set to: {active_sell_price}. Trailing value: {trailing_value}")
sleep(60)
while True:
    sell_price, _ = exchange.get_actual_price(currency)

    # if price goes above active sell price -> increate trailing
    if sell_price > active_sell_price:
        active_sell_price = sell_price
        logging.info(f"Trailing limit increased. Crypto to be sold at: {round(active_sell_price - trailing_value, 3)}")
        sleep(60)

    # if price goes DOWN below trailing stop -> sell the order
    elif sell_price < active_sell_price - trailing_value:
        logging.debug(f"Actual price {sell_price} is lower as trailing price {round(active_sell_price - trailing_value, 3)}. Selling.")
        r = exchange.sell_instant(currency + "eur", amount)
        break

    # if price goes DOWN but not below trailing stop -> do nothing
    else:
        logging.debug(
            f"Trailing active. Sell pri {round(active_sell_price - trailing_value, 3)}, teraz {sell_price}")
        sleep(60)

