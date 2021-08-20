#!/usr/bin/env python3

from exchanges import Gemini
import argparse
import logging
from time import sleep
import random

parser = argparse.ArgumentParser()
parser.add_argument('action', type=str, help="Possible action: buy/audit/withdraw")
parser.add_argument('crypto', type=str, help="Possible crypto: btc/eth")
args = parser.parse_args()
action = args.action
crypto = args.crypto

# filename="/home/pi/Desktop/BitStampAPI/logs/gemini.log"
logging.basicConfig(filename="gemini.log",
                    filemode="a",
                    format="%(asctime)s - %(message)s",
                    level="INFO")

gemini = Gemini("example")

if str(action).lower() == "buy":
    sleep(random.randint(10,200))
    buy = gemini.buy_limit(f"{crypto}eur", 5)
    logging.info(f"Crypto buy: {buy['order_id']}, {buy['original_amount']}, {buy['price']}")
elif str(action).lower() == "audit":
    addded = gemini.fill_sheet_file(f"{crypto}eur")
    logging.info(f"Document update: {addded} rows added.")
elif str(action).lower() == "withdraw":
    withdraw = gemini.withdraw_to_wallet(crypto)
    logging.info(f"{str(crypto).upper()} withdrawal of {withdraw['amount']} to {withdraw['address']}")

else:
    print("No valid action.")
    logging.error("Action incorrect. Choose: buy / action")