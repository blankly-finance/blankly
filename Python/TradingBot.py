import Keys
import Utils
import time
import sys
from Server import TradeInterface as TI


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
utils = Utils.Utils()
Server = TI()


Server.init_coinbase_pro()
Server.add_exchange("bill", API_KEY, API_SECRET, API_PASS)
print(Server.get_exchange_state("bill"))
sys.exit()





bitcoinTicker = Tickers("BTC-USD", show=False)
time.sleep(2)

"""you always quit as soon as the going gets tough"""

print(call.getAccounts())
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
exchange.getFee(show=True)
print("Value:")
print(exchange.getValueAtTime())
print("Profitable")
exchange.getProfitableSellPrice(show=True)
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
    print(exchange.isProfitable(show=True))
    time.sleep(1)
    utils.getPriceDerivative(bitcoinTicker, 10)

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