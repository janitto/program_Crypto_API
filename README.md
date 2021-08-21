# Toolkit for using REST API of crypto exchanges

Hello, this is a toolkit for using functiones of crypto exchanges **Bitstamp**, **Gemini** and **Kraken**. You will be able to operate over your account using your own software.

## Installation

[Clone](https://github.com/git-guides/git-clone) the repository.

```bash
git clone https://github.com/janitto/program_Crypto_API.git
```

Install requirements.txt

```python
pip install -r requirements.txt
```

Configure personal metadata in the file: "*program_Crypto_API/trading_bots/meta_login_example.json*" and replace word *example* with your name.

## Usage
List of Exchanges included in the package:
* Gemini
* Bitstamp
* Kraken

## Functions
Same functions are available across each exchange.

```python
from exchanges import Gemini, Kraken, Bitstamp

exchange= Gemini("example")
exchange= Bitstamp("example")
exchange= Kraken("example")

# list of functions
a = exchange.get_actual_price("btc")
b = exchange.buy_limit("btceur", 5, 39000)
c = exchange.buy_instant("btceur", 5)
d = exchange.show_open_orders()
e = exchange.check_status(123456789)
f = exchange.cancel_oder(123456789)
g = exchange.get_balance()
h = exchange.get_amount_bought(123456789)
i = exchange.withdraw_to_wallet("btc")
j = exchange.show_transactions("btc")
k = exchange.fill_sheet_file("btc")
```

## Currently implemented

|  | Gemini  |Bitstamp | Kraken |
| ------------- | :-------------: | :-------------: | :-------------: |
| get_actual_price  | * | * | * |
| buy_limit         | * | * |   |
| buy_instant       | * | * |   |
| show_open_orders  | * | * |   |
| check_status      | * | * |   |
| cancel_oder       | * | * |   |
| get_balance       | * | * |   |
| get_amount_bought | * | * |   |
| withdraw_to_wallet| * | * |   |
| show_transactions | * | * |   |
| fill_sheet_file   | * | * |   |

## Strategies

### dollar_cost_average.py _"action"_ _"spend_eur"_ "_crypto_"

Strategy for periodical buys auditing and withdrawing of crypto from exchanges.


**action(str)** -> buy / audit / withdraw  
**spend_eur(float)** -> amount of EUR to spend (only in a buy)  
**crpto(str)** -> symbol of crypto  

Example:  
dollar_cost_average.py "buy" 5 "btc"  
dollar_cost_average.py "audit" "btc"  
dollar_cost_average.py "withdraw" "btc"  

(for audit configure connection to google spreadsheets)  
(for withdraw enter your public addresses to metadata)

### trailing_stop_sell.py

Strategy for setting a guaranteed minimal sell price, which will automatically increase, if price of crypto increase.

**currency(str)** -> symbol of crypto  
**amount(float)** -> amount of crypto to be sold  
**trailing(float)** -> if price drops by more than stated %, sell is initiated.  

Example:  
trailing_stop_sell.py "ltc" 1 10

Let's say current price of LTC is 120 € /LTC, and you execute command above.
Trailing price is set to 120*10% = 12 €
If price of LTC decrease to 108 €, 1 LTC is sold.
If price of LTC increase to 130 €, trailing threshold (currently 108 €) will be increased to 118 € (130 € - 12 €).
If price of LTC drop then to 120 €, nothing will happen, but if drops to 118 €, 1 LTC is sold.