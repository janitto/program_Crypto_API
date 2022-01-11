#!/usr/bin/env python3

from bin.exchanges import Gemini, Bitstamp, Kraken
import argparse
import logging
from time import sleep
import random

parser = argparse.ArgumentParser()
parser.add_argument('user', type=str, help="User name")
parser.add_argument('exchange', type=str, help="Exchange name")
parser.add_argument('action', type=str, help="Possible action: buy/audit/withdraw")
parser.add_argument('spend_eur', type=float, help="Amount of EUR to spend")
parser.add_argument('crypto', type=str, help="Possible crypto: btc/eth/...")
args = parser.parse_args()
user = args.user
exchange = args.exchange
action = args.action
spend_eur = args.spend_eur
crypto = args.crypto

logging.basicConfig(filename=f"logs/{exchange}_{crypto}_{user}_DCA_logfile.log",
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

if str(action).lower() == "buy":
    sleep(random.randint(10,200))
    buy = exchange.buy_limit(f"{crypto}eur", spend_eur)
    if exchange.lower() == "gemini":
        logging.info(f"GEMINI Crypto buy: {buy['order_id']}, {buy['original_amount']}, {buy['price']}")
    elif exchange.lower() == "kraken":
        logging.info(f"KRAKEN Crypto buy: {buy['result']['txid']}, {buy['result']['descr']}")
    elif exchange.lower() == "bitstamp":
        pass
    else:
        logging.info(buy)

elif str(action).lower() == "audit":
    addded = exchange.fill_sheet_file(f"{crypto}eur", "Analytics")
    logging.info(f"Document update: {addded} rows added.")

elif str(action).lower() == "withdraw":
    withdraw = exchange.withdraw_to_wallet(crypto)
    logging.info(f"{str(crypto).upper()} withdrawal of {withdraw['amount']} to {withdraw['address']}")

else:
    logging.error(f"Action {action} incorrect. Choose: - buy / withdraw / audit - action")