# Toolkit for using REST API of crypto exchanges

Hello, this is a toolkit for using functiones of crypto exchanges Bitstamp, Gemini and Kraken. You will be able to operate over your account using your own software.

## Installation

[Clone](https://github.com/git-guides/git-clone) the repository.

```bash
git clone https://github.com/janitto/program_Crypto_API.git
```

Install requirements.txt

```python
pip install -r requirements.txt
```

Configure personal metadata in file: "*program_Crypto_API/trading_bots/meta_login_example.json*" and replace word *example* with your name.

## Usage
List of Exchanges included in te package:
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


