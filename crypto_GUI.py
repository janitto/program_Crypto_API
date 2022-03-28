from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from bin.exchanges import Kraken
from datetime import datetime
import pyqtgraph as pg
import time
import requests

class MyGUI(QMainWindow):

    def __init__(self):
        super(MyGUI, self).__init__()
        uic.loadUi("bin/template.ui", self)
        self.exchange = Kraken(name="jany")
        self.currency = self.get_currency()

        self.graphWidget = pg.PlotWidget(self)
        self.graphWidget.setGeometry(310, 420, 340, 100)
        self.graphWidget.setBackground('w')

        self.show()

        self.balancesRefresh.clicked.connect(self.refresh_balances)
        self.balancesRefresh.clicked.connect(self.refresh_chart)
        self.tradesRefresh.clicked.connect(self.refresh_trades)

    def refresh_balances(self):
        self.currency = self.get_currency()
        if self.currency in ("ada", "dot"):
            self.currency = self.currency + ".s"
        balance = self.exchange.get_balance(self.currency)
        self.balanceLabel.setText("Balance: " + str(balance))

    def refresh_chart(self):
        self.graphWidget.clear()
        self.currency = self.get_currency()
        params = {"symbol": f"{self.currency.upper()}EUR",
                  "interval": "30m",
                  "startTime": int(time.time() * 1000) - 604800000,
                  "endTime": int(time.time() * 1000)}
        r = requests.get("https://api.binance.com/api/v3/klines", params=params)
        r = r.json()
        prices = []
        for day in r:
            prices.append(float(day[4]))


        self.graphWidget.plot(prices)


    def refresh_trades(self):
        self.currency = self.get_currency()
        self.tradesTable.clearContents()
        trades = self.exchange.show_transactions(f"{self.currency}eur")

        row = 0
        for trade in trades:
            if row < 10:
                self.tradesTable.setItem(row, 0, QTableWidgetItem(str(datetime.fromtimestamp(trade['time']).date())))
                self.tradesTable.setItem(row, 1, QTableWidgetItem(trade["type"]))
                self.tradesTable.setItem(row, 2, QTableWidgetItem(trade["price"]))
                self.tradesTable.setItem(row, 3, QTableWidgetItem(str(round(float(trade["vol"]),4))))
                row += 1
            self.tradesTable.resizeColumnsToContents()

    def get_currency(self):
        if self.tradesTRX.isChecked():
            return "trx"
        elif self.tradesADA.isChecked():
            return "ada"
        elif self.tradesDOT.isChecked():
            return "dot"
        elif self.tradesETH.isChecked():
            return "eth"
        else:
            return "btc"

app = QApplication([])
window = MyGUI()
app.exec_()
