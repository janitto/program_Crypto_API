# Toolkit for using REST API of crypto exchanges

Hello, this is a toolkit for using functiones of crypto exchanges **Bitstamp**, **Gemini** and **Kraken**. You will be able to operate over your account using your own software.

## Installation

[Clone](https://github.com/git-guides/git-clone) the repository.

``` bash
git clone https://github.com/janitto/program_Crypto_API.git
```

Install modules:

``` python
pip install requests gspread oauth2client pandas
pip install flask flask-restful markdown2 pygments
```

Download [NGROK](https://ngrok.com/download). Utility for tunneling your ports to internet.

Configure personal metadata in the file: "*program_Crypto_API/meta_login_example.json*" and replace a word *example* with your name.

## Usage

List of Exchanges included in the package:

* Gemini
* Bitstamp
* Kraken

Run the _"crypto_api.py"_ in the background.
``` bash
nohup crypto_api.py &
```

Run the ngrok
``` bash
ngrok http -auth "username:password" -region=eu 7777
```

## Functions

Same functions are available across each exchange.

``` python
from exchanges import Gemini, Kraken, Bitstamp


exchange= Gemini("example")  
exchange= Bitstamp("example")  
exchange= Kraken("example")  
```

## List of functions

``` python
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

|  |                                      Gemini                                       |                                       Bitstamp                                        |                                      Kraken                                       | Audit |
| ------------- |:---------------------------------------------------------------------------------:|:-------------------------------------------------------------------------------------:|:---------------------------------------------------------------------------------:| :-------------: |
| get_actual_price  |                                        OK                                         |                                          OK                                           |                                        OK                                         |   |
| buy_limit         |                                        OK                                         |                                          OK                                           |                                        OK                                         |   |
| buy_instant       |                                        OK                                         |                                          OK                                           |                                        OK                                         |   |
| show_open_orders  |                                        OK                                         |                                          OK                                           |                                        OK                                         |   |
| check_status      |                                        OK                                         |                                          OK                                           |                                        OK                                         |   |
| cancel_oder       |                                        OK                                         |                                          OK                                           |                                        OK                                         |   | 
| get_balance       |                                        OK                                         |                                          OK                                           |                                        OK                                         |  |
| get_amount_bought |                                        OK                                         |                                          OK                                           |                                        OK                                         |   |
| withdraw_to_wallet|                                         *                                         |                                          OK                                           |                                                                                   |   |
| show_transactions |                                        OK                                         |                                          OK                                           |                                        OK                                         |  |
| fill_sheet_file   |                                        OK                                         |                                           *                                           |                                                                                   |   |
| REST API | [balance](/balance/<user>/gemini) / [trades](/trades_over_time/<user>/gemini/btc) | [balance](/balance/<user>/bitstamp) / [trades](/trades_over_time/<user>/bitstamp/btc) | [balance](/balance/<user>/kraken) / [trades](/trades_over_time/<user>/kraken/btc) |
| Audit |                     [Gemini audit](/audit/<user>/gemini/btc)                      |                     [Bitstamp audit](/audit/<user>/bitstamp/btc)                      |                     [Kraken audit](/audit/<user>/kraken/btc)                      |  |
## Strategies

### 1. dollar_cost_average.py (action="" spend_eur="" crypto="")

Strategy for periodical buys auditing and withdrawing of crypto from exchanges.


**action(str)** -> buy / audit / withdraw  
**spend_eur(float)** -> amount of EUR to spend (only in a buy)  
**crpto(str)** -> symbol of crypto  

Example:  

``` bash
nohup python dollar_cost_average.py "buy" 5 "btc" &
nohup python dollar_cost_average.py "audit" "btc" &
nohup python dollar_cost_average.py "withdraw" "btc" &
```
 

Set up a kron job with defined parameters to enjoy DCA.

(for an audit configure connection to google spreadsheets)  
(for withdraw enter your public addresses to metadata)

### 2. trailing_stop_sell.py (currency="" amount="" trailing="")

Strategy for setting a guaranteed minimal sell price, which will automatically increase, if price of crypto increase.

**currency(str)** -> symbol of crypto  
**amount(float)** -> amount of crypto to be sold  
**trailing(float)** -> if price drops by more than stated %, sell is initiated.  

``` bash
trailing_stop_sell.py "ltc" 1 10
```

Let's say current price of LTC is 120 EUR /LTC, and you execute command above.
Trailing price is set to 120*10% = 12 EUR
If price of LTC decrease to 108 EUR, 1 LTC is sold.
If price of LTC increase to 130 EUR, trailing threshold (currently 108 EUR) will be increased to 118 EUR (130 EUR - 12 EUR).
If price of LTC drop then to 120 EUR, nothing will happen, but if drops to 118 EUR, 1 LTC is sold.

### 3. buy_low_sell_high.py (currency="", threshold="")

Strategy, which buy if price drops by defined threshold and then sell if price increase by defined threshold.

**currency(str)** -> symbol of crypto  
**threshold(float)** -> threshold % in decimal

``` bash
nohup python buy_low_sell_high.py "BAT" 0.05 &
```

If threshold is set to 0.05, then script will buy crypto if current price is lower by more than threshold.
Then is sold when crypto increase by same amount.