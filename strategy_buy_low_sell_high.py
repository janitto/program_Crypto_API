#!/usr/bin/env python3

from bin.exchanges import Bitstamp, Kraken, Gemini, send_mail
from statistics import mean
from time import sleep
import logging
import argparse
import datetime

parser = argparse.ArgumentParser()
parser.add_argument('exchange', type=str, help="Define exchange.")
parser.add_argument('currency', type=str, help="Define currency to trade.")
parser.add_argument('buyif', type=float, help="Buy if price decrease %")
parser.add_argument('sellif', type=float, help="TSell if price rise %")
args = parser.parse_args()
exchange = args.exchange
curr = args.currency
buyif = args.buyif
sellif = args.sellif

logging.basicConfig(filename=f"logs/{exchange}_{curr}_content_log.log",
                    filemode="a",
                    format="%(asctime)s - %(message)s",
                    level="INFO")

THRESHOLD_BUY = buyif                       #decimal format of % which if decrease, then buy
THRESHOLD_SELL = sellif                     #decimal format of % which if increase, then sell
INVESTMENT = 20                             #investment in EUR
CHECK_INTERVAL = 300                        #interval of price check in seconds
TURNAROUND_PERIOD = 86400                   #86400 seconds is 1 day
EXCHANGE_FEE = 0.00                         #fee for trade %
EXCHANGE_COMMISION = 1 - EXCHANGE_FEE	    #remainer after deducing fee

if exchange.lower() == "bitstamp":
    exchange = Bitstamp(name="example")
elif exchange.lower() == "kraken":
    exchange = Kraken(name="example")
elif exchange.lower() == "gemini":
    exchange = Gemini(name="example")
else:
    logging.error("Wrong exchange defined as arg1")


def start_bot(currency, total_investments=3):
    prices = []
    kupene = []
    kupene_id = []
    while True:
        price_bid, price = exchange.get_actual_price(currency)
        logging.debug(f"bid: {price_bid} ask: {price}")

        if price == 0 or price_bid == 0:
            logging.error("Can not get pice.")
            sleep(CHECK_INTERVAL)               #sometimes give API DNS error, so in such case, skip the check.
            continue

        prices.append(price)

        if len(prices) > TURNAROUND_PERIOD/CHECK_INTERVAL:
            del prices[0]                   #delete first price, as it is older than turnarounf period
        avg = mean(prices)

        if price < avg*(1-THRESHOLD_BUY):
            if True:
                if len(kupene) < total_investments:
                    logging.info(f"Buying at price: {price}")
                    r = exchange.buy_instant(currency+"eur", INVESTMENT)
                    kupene.append(price)
                    kupene_id.append(r["id"])
                    prices.clear()                  #if buy, then reset avg price, so another same buy is not processed.
                    send_mail(currency,
                              price,
                              "bought",
                              f"Bought {currency.upper()} at price {price}.\n"
                              f"Price {price} is smaller than avg price {round(avg,2)} lowerred by {THRESHOLD_BUY*100}% to threshold {round(avg*(1-THRESHOLD_BUY),2)}.\n"
                              f"Currently purchased:{kupene}\n"
                              f"IDs: {kupene_id}")
                else:
                    logging.warning("No budget left.")

        elif kupene:
            if price_bid > min(kupene)*(1+THRESHOLD_SELL):
                price = price_bid
                index = kupene.index(min(kupene))
                transaction_id = kupene_id[index]
                amount = exchange.get_amount_bought(currency, transaction_id)
                logging.debug(f"Pri trailingu predam {amount}")
                r = exchange.sell_instant(currency+"eur", amount)
                transaction_id = r["id"]
                zarobene = float(r["amount"])*float(r["price"])*EXCHANGE_COMMISION - INVESTMENT*EXCHANGE_COMMISION
                kurz_predaja = float(r["price"])
                logging.info(f"Kupena krypto v kurze {min(kupene)} vzrastla o {round(kurz_predaja/min(kupene)-1, 2)*100}%.\n"
                             f"Predal som v kurze {kurz_predaja}\n"
                             f"Zarobil som: {round(zarobene,3)} EUR\n"
                             f"TransID: {transaction_id}")
                send_mail(currency,
                          kurz_predaja,
                          "sold",
                          f"Crypto bought at {min(kupene)} incrased by {round(kurz_predaja/min(kupene)-1, 2)*100}%.\n"
                          f"sold at price {kurz_predaja}\n"
                          f"Earned: {round(zarobene,3)} EUR\n"
                          f"TransID: {transaction_id}")

                with open("logs/earnings.csv", "a") as f:
                    f.write(f"{datetime.datetime.now().strftime('%X')},{currency},{min(kupene)},{kurz_predaja},{round(zarobene,3)},{transaction_id}\n")
                    f.close()

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
    start_bot(curr)
