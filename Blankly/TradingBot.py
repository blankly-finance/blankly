"""
    Main script for testing some internal library functions
    Copyright (C) 2021  Emerson Dove

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU Lesser General Public License as published
    by the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU Lesser General Public License for more details.

    You should have received a copy of the GNU Lesser General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.
"""

import utils
import time
from Server import TradeInterface as TI
from Coinbase_Pro.Coinbase_Pro_API import API
from Coinbase_Pro.Coinbase_Pro import Coinbase_Pro


""" Define secret keys """
API_KEY = Keys.API_KEY
API_SECRET = Keys.API_SECRET
API_PASS = Keys.API_PASS


""" Define used currencies """
currencies = ["BTC", "XLM"]
market = "USD"

""" Define known best buy times """
buys = ["2:00"]
sells = ["21:00"]

""" Define libraries & Connections """
utils = utils.Utils()
Server = TI()

# exchange = Coinbase_Pro("bill", {}, [API_KEY, API_SECRET, API_PASS])


# print("State:")
# exchange.append_model("COMP")
# print(exchange.get_portfolio_state())
# print("State with everything:")
# print("Started Model")
# exchange.start_models()
Server.init()
Server.add_exchange("API Portfolio", "coinbase_pro", [API_KEY, API_SECRET, API_PASS])
# calls = API(API_KEY, API_SECRET, API_PASS)
print(Server.get_portfolio_state("API Portfolio"))
Server.assign_model("API Portfolio", "Bill's Model", "COMP")
# print(calls.getPortfolio())
# print(Server.get_exchange_state("API Portfolio"))
Server.run_model("API Portfolio")
while True:
    print(Server.get_portfolio_state("API Portfolio"))
    time.sleep(1)

sys.exit()





bitcoinTicker = Tickers("BTC-USD", show=False)
time.sleep(2)

"""you always quit as soon as the going gets tough"""

print(call.get_portfolio())
print(call.getAccountInfo('GRT-USD'))
sys.exit()


ids = 0
def nextId():
    global ids
    ids += 1
    return {
        "id": ids
    }


manager = ProfitManager("BTC", bitcoinTicker)


# fit = utils.fitParabola(bitcoinTicker, 10000)
manager.addExchange(Exchange.Exchange(utils.generateMarketOrder(.001, "buy", "BTC-USD"), bitcoinTicker))

# Main thread becomes I/O thread
while True:
    command = input("View LocalAccount (v) or sell exchange 0 (s):")
    if command == "v":
        print("USD: " + str(LocalAccount.account["USD"]))
        print("BTC: " + str(LocalAccount.account["BTC-USD"]))
    elif command == "s":
        manager.getExchange(0).sellSelf()
        print("Selling all: ")
        print("USD: " + str(LocalAccount.account["USD"]))
        print("BTC: " + str(LocalAccount.account["BTC-USD"]))
    else:
        print("Command not found")

sys.exit()
print("Fee:")
exchange.get_fee(show=True)
print("Value:")
print(exchange.get_value_at_time())
print("Profitable")
exchange.is_profitable_buy(show=True)
sys.exit()

# print(utils.getPriceDerivative(bitcoinTicker, 1000))
#
# while True:
#     time.sleep(1)
#
# order = utils.generateLimitOrder(Constants.MINIMUM_TO_SET_LIMIT, 15000, "buy", "BTC-USD")
# response, exchange = call.placeOrder(order, bitcoinTicker, show=True)
# print("Placed order")
# time.sleep(5)
# orders = call.getOpenOrders(show=True)
# print("Open Orders")
# print(orders)
# print("Canceling order")
# exchange.cancelOrder()
# time.sleep(3)
# print(exchange.confirmCanceled())
#
# while True:
#     time.sleep(1)


# order = utils.generateLimitOrder(Constants.MINIMUM_TO_SET_LIMIT, 15000, "buy", "BTC-USD")
# response, exchange = call.placeOrder(order, bitcoinTicker, show=True)

response = {
    'id': 3
}
call.getAccountInfo("BTC", "balance")
sys.exit()
exchange = Exchange.Exchange("buy", 46, bitcoinTicker, response, call)
while True:
    print(exchange.is_profitable(show=True))
    time.sleep(1)
    utils.get_price_derivative(bitcoinTicker, 10)

""" Main trade loop """
scheduler = sched.scheduler(time.time, time.sleep)

def tradeFunction(id):
    print("started at " + str(time.time()))
    counter = 0
    while counter < 5:
        print("Trading " + id + ": " + str(counter))
        time.sleep(1)
        counter += 1
    print("finished at " + str(time.time()))


schedule.every().minute.at(":00").do(tradeFunction, "no1")
schedule.every().minute.at(":02").do(tradeFunction, "no1")

while True:
    schedule.run_pending()
    time.sleep(1)