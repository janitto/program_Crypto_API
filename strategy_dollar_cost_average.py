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
parser.add_argument('--spend_eur', type=float, help="Amount of EUR to spend")
parser.add_argument('--crypto', type=str, help="Possible crypto: btc/eth/...")
args = parser.parse_args()
user = str(args.user).lower()
exchange = args.exchange
action = args.action
spend_eur = args.spend_eur
crypto = args.crypto

logging.basicConfig(filename=f"logs/{exchange}_{user}_DCA_logfile.log",
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
    if spend_eur is None or crypto is None:
        logging.error("No SPEND_EUR or CRYPTO defined.")
    else:
        buy = exchange.buy_limit(f"{crypto}eur", spend_eur)
        logging.info(f"{args.exchange.upper()} Crypto buy: {buy}")

elif str(action).lower() == "audit":
    if crypto is None:
        logging.error("No CRYPTO defined")
    else:
        addded = exchange.fill_database(f"{crypto}eur")
        logging.info(f"{args.exchange.upper()} Database update: {addded}")

elif str(action).lower() == "withdraw":
    if crypto is None:
        logging.error("No CRYPTO defined")
    else:
        withdraw = exchange.withdraw_to_wallet(crypto)
        logging.info(f"{args.exchange.upper()} {str(crypto).upper()} withdrawal: {withdraw}")

else:
    logging.error(f"Action {action} incorrect. Choose: - buy / withdraw / audit - action")