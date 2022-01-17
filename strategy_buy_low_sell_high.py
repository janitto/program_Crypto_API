#!/usr/bin/env python3

from bin.exchanges import Bitstamp, Kraken, Gemini
from statistics import mean
from time import sleep
import logging
import argparse

parser = argparse.ArgumentParser()
parser.add_argument('user', type=str, help="User name")
parser.add_argument('exchange', type=str, help="Exchange name")
parser.add_argument('currency', type=str, help="Define currency to trade.")
parser.add_argument('buyif', type=float, help="Buy if price decrease %")
parser.add_argument('sellif', type=float, help="Sell if price rise %")
args = parser.parse_args()
user = args.user
exchange = args.exchange
currency = args.currency
buyif = args.buyif
sellif = args.sellif

logging.basicConfig(filename=f"logs/{exchange}_{user}_BLSH_logfile.log",
                    filemode="a",
                    format="%(asctime)s - %(message)s",
                    level="INFO")

THRESHOLD_BUY = buyif                       #decimal format of % which if decrease, then buy (1% = 0.01)
THRESHOLD_SELL = sellif                     #decimal format of % which if increase, then sell
INVESTMENT = 5                              #investment in EUR
CHECK_INTERVAL = 300                        #interval of price check in seconds
TURNAROUND_PERIOD = 86400                   #86400 seconds is 1 day
EXCHANGE_FEE = 0.0026                       #fee for trade % (1% = 0.01)
EXCHANGE_COMMISION = 1 - EXCHANGE_FEE	    #remainer after deducing fee

if exchange.lower() == "bitstamp":
    exchange = Bitstamp(name=user)
elif exchange.lower() == "kraken":
    exchange = Kraken(name=user)
elif exchange.lower() == "gemini":
    exchange = Gemini(name=user)
else:
    logging.error("Wrong exchange defined as arg2")


def start_bot(currency, total_investments=3):
    prices = []
    kupene = []
    kupene_id = []
    while True:
        price_bid, price = exchange.get_actual_price(currency)
        logging.debug(f"bid: {price_bid} ask: {price}")

        if price == 0 or price_bid == 0:
            logging.warning("Can not get price.")
            sleep(CHECK_INTERVAL)               #sometimes give API DNS error, so in such case, skip the check.
            continue

        prices.append(price)

        if len(prices) > TURNAROUND_PERIOD/CHECK_INTERVAL:
            del prices[0]                       #delete first price, as it is older than turnarounf period
        avg = mean(prices)

        if price < avg*(1-THRESHOLD_BUY):
            if True:
                if len(kupene) < total_investments:
                    logging.info(f"Buying at price: {price}")
                    r = exchange.buy_instant(currency+"eur", INVESTMENT)
                    kupene.append(price)
                    if args.exchange == "bitstamp": kupene_id.append(r["id"])
                    if args.exchange == "kraken": kupene_id.append(r["result"]["txid"])
                    if args.exchange == "gemini": kupene_id.append(r["order_id"])
                    prices.clear()                  #if buy, then reset avg price, so another same buy is not processed.

                else:
                    logging.warning(f"{total_investments} investments already made. No more...")

        elif kupene:
            if price_bid > min(kupene)*(1+THRESHOLD_SELL):
                price = price_bid
                index = kupene.index(min(kupene))
                transaction_id = kupene_id[index]
                amount = exchange.get_amount_bought(currency, transaction_id)
                logging.info(f"Selling {amount} of {currency}")
                r = exchange.sell_instant(currency+"eur", amount)
                logging.info(r)

                kupene.remove(min(kupene))
                del kupene_id[index]
        else:
            pass

        logging.info(f"Nr. of controlled prices: {len(prices)} Current price: {price} Avg price: {round(avg,3)}")
        logging.debug(f"Recently bought: {kupene}")
        logging.debug(f"IDs: {kupene_id}")
        logging.debug("-------")
        sleep(CHECK_INTERVAL)


if __name__ == "__main__":
    start_bot(currency)
