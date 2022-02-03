from PyQt5 import uic
from PyQt5.QtWidgets import QApplication, QMainWindow, QTableWidgetItem
from bin.exchanges import Kraken
from datetime import datetime
import os

class MyGUI(QMainWindow):

    def __init__(self):
        super(MyGUI, self).__init__()
        print(os.listdir())
        uic.loadUi("bin/template.ui", self)
        self.exchange = Kraken(name="jany")
        self.show()

        self.balancesRefresh.clicked.connect(self.refresh_balances)
        self.tradesRefresh.clicked.connect(self.refresh_trades)

    def refresh_balances(self):
        if self.tradesTRX.isChecked():
            balance = self.exchange.get_balance("trx")
        if self.tradesADA.isChecked():
            balance1 = self.exchange.get_balance("ada")
            balance2 = self.exchange.get_balance("ada.s")
            if balance1 >= balance2:
                balance = balance1
            else:
                balance = balance2
        if self.tradesDOT.isChecked():
            balance1 = self.exchange.get_balance("dot")
            balance2 = self.exchange.get_balance("dot.s")
            if balance1 >= balance2:
                balance = balance1
            else:
                balance = balance2
        if self.tradesBTC.isChecked():
            balance = self.exchange.get_balance("btc")
        if self.tradesETH.isChecked():
            balance = self.exchange.get_balance("eth")

        self.balanceLabel.setText("Balance: " + str(balance))

    def refresh_trades(self):
        self.tradesTable.clearContents()
        if self.tradesTRX.isChecked():
            trades = self.exchange.show_transactions("trxeur")
        if self.tradesADA.isChecked():
            trades = self.exchange.show_transactions("adaeur")
        if self.tradesDOT.isChecked():
            trades = self.exchange.show_transactions("doteur")
        if self.tradesBTC.isChecked():
            trades = self.exchange.show_transactions("btceur")
        if self.tradesETH.isChecked():
            trades = self.exchange.show_transactions("etheur")

        row = 0
        for trade in trades:
            if row < 10:
                self.tradesTable.setItem(row, 0, QTableWidgetItem(str(datetime.fromtimestamp(trade['time']).date())))
                self.tradesTable.setItem(row, 1, QTableWidgetItem(trade["type"]))
                self.tradesTable.setItem(row, 2, QTableWidgetItem(trade["price"]))
                self.tradesTable.setItem(row, 3, QTableWidgetItem(str(round(float(trade["vol"]),4))))
                row += 1
            self.tradesTable.resizeColumnsToContents()

    def mouseMoveEvent(self, e):
        self.label.setText("mouseMoveEvent")

app = QApplication([])
window = MyGUI()
app.exec_()
