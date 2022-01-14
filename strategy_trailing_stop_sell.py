#!/usr/bin/env python3

from bin.exchanges import Gemini, Bitstamp, Kraken
import argparse
import logging
from time import sleep


parser = argparse.ArgumentParser()
parser.add_argument('user', type=str, help="User name")
parser.add_argument('exchange', type=str, help="Exchange name")
parser.add_argument('currency', type=str, help="Possible crypto: btc/eth/...")
parser.add_argument('amount', type=float, help="Amount to sell in crypto")
parser.add_argument('trailing', type=float, help="How much % od drop before you sell (10 for 10%)")
args = parser.parse_args()
user = str(args.user).lower()
exchange = args.exchange
currency = args.currency
amount = args.amount
trailing = args.trailing


logging.basicConfig(filename=f"logs/{exchange}_{user}_TS_logfile.log",
                    filemode="a",
                    format="%(asctime)s - %(message)s",
                    level="INFO")

if exchange.lower() == "bitstamp":
    exchange = Bitstamp(name=user)
elif exchange.lower() == "kraken":
    exchange = Kraken(name=user)
elif exchange.lower() == "gemini":
    exchange = Gemini(name=user)
else:
    logging.error("Wrong exchange defined as arg2")

# Trailing value: how much could crypto drop. In real currency.
# Trailing price: sell price

have_currency = exchange.get_balance(currency)
if have_currency > amount:
    logging.info(f"Have {have_currency}, going to trail sell {amount}.")
    active_sell_price, _ = exchange.get_actual_price(currency)
    trailing_value = round(active_sell_price * trailing / 100, 4)
    logging.info(f"Current price set to: {active_sell_price} Trailing value: {trailing_value}")
    sleep(60)
    while True:
        sell_price, _ = exchange.get_actual_price(currency)

        # if price goes ABOVE active sell price -> increase trailing
        if sell_price > active_sell_price:
            active_sell_price = sell_price
            logging.info(f"Trailing price increased. Crypto will be sold at: {round(active_sell_price - trailing_value, 4)}")
            sleep(60)

        # if price goes DOWN below trailing price -> sell the order
        elif sell_price < active_sell_price - trailing_value:
            logging.info(f"Current price {sell_price} is lower as trailing price {round(active_sell_price - trailing_value, 4)}. Selling.")
            r = exchange.sell_instant(currency + "eur", amount)
            sleep(10)
            logging.info(r)
            break

        # if price goes DOWN but not below trailing stop -> do nothing
        else:
            logging.debug(
                f"Trailing active. Trailing price {round(active_sell_price - trailing_value, 3)}, now {sell_price}")
            sleep(60)
else:
    logging.error(f"Cant start. Want to trade with {amount}, but have only {have_currency} {currency.upper()}.")

