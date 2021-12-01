#!/usr/bin/env python3

from bin.exchanges import Gemini, Bitstamp, Kraken
import argparse
import logging
from time import sleep
import random

parser = argparse.ArgumentParser()
parser.add_argument('action', type=str, help="Possible action: buy/audit/withdraw")
parser.add_argument('spend_eur', type=float, help="Amountof EUR to spend")
parser.add_argument('crypto', type=str, help="Possible crypto: btc/eth/...")
args = parser.parse_args()
action = args.action
spend_eur = args.amount
crypto = args.crypto

logging.basicConfig(filename="logs/DCA_logfile.log",
                    filemode="a",
                    format="%(asctime)s - %(message)s",
                    level="INFO")

exchange = Gemini("example")
#exchange = Bitstamp("example")
#exchange = Kraken("example")

if str(action).lower() == "buy":
    sleep(random.randint(10,200))
    buy = exchange.buy_limit(f"{crypto}eur", spend_eur)
    logging.info(f"Crypto buy: {buy['order_id']}, {buy['original_amount']}, {buy['price']}")
elif str(action).lower() == "audit":
    addded = exchange.fill_sheet_file(f"{crypto}eur")
    logging.info(f"Document update: {addded} rows added.")
elif str(action).lower() == "withdraw":
    withdraw = exchange.withdraw_to_wallet(crypto)
    logging.info(f"{str(crypto).upper()} withdrawal of {withdraw['amount']} to {withdraw['address']}")

else:
    logging.error(f"Action {action} incorrect. Choose: - buy / withdraw / audit - action")