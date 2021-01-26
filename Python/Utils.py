import json, numpy, time, LocalAccount
from sklearn.linear_model import LinearRegression
import iso8601

"""
Order Place Example:
order = {
    'size': 1.0,
    'price': 1.0,
    'side': 'buy',
    'product_id': 'BTC-USD',
}
"""


class Utils:
    @staticmethod
    def tradeLocal(buyOrSell, currency, exchangeAmount, ticker):
        if buyOrSell == "sell":
            LocalAccount.account["USD"] = float(ticker.getMostRecentTick()["price"]) * exchangeAmount + LocalAccount.account["USD"]
            LocalAccount.account[currency] = LocalAccount.account[currency] - exchangeAmount

        else:
            LocalAccount.account["USD"] = LocalAccount.account["USD"] - float(ticker.getMostRecentTick()["price"]) * exchangeAmount
            LocalAccount.account[currency] = LocalAccount.account[currency] + exchangeAmount

    def __init__(self):
        pass

    """ 
    Json pretty printer for show arguments
    """
    def printJSON(self, jsonObject):
        out = json.dumps(jsonObject.json(), indent=2)
        print out

    """
    Size: Amount of base currency to buy or sell
    Price: Price per bitcoin
    Ex: Buy .001BTC at $15,000 is generateLimitOrder(.001, 15000, "buy", "BTC-USD")
    """
    def generateLimitOrder(self, size, price, side, product_id):
        order = {
            'size': size,
            'price': price,
            'side': side,
            'product_id': product_id,
        }
        return order

    """
    Size: Amount of base currency to buy or sell
    """
    def generateMarketOrder(self, size, side, product_id):
        order = {
            'size': size,
            'side': side,
            'product_id': product_id,
        }
        return order

    def getEpochFromISO8601(self, ISO8601):
        return time.mktime(iso8601.parse_date(ISO8601).timetuple())


    """
    Performs regression n points back
    """
    def getPriceDerivative(self, ticker, pointNumber):
        feed = numpy.array(ticker.getTickerFeed()).reshape(-1, 1)
        times = numpy.array(ticker.getTimeFeed()).reshape(-1, 1)
        if pointNumber > len(feed):
            pointNumber = len(feed)

        feed = feed[-pointNumber:]
        times = times[-pointNumber:]
        prices = []
        for i in range(pointNumber):
            prices.append(feed[i][0]["price"])
        prices = numpy.array(prices).reshape(-1, 1)

        regressor = LinearRegression()
        regressor.fit(times, prices)
        regressor.predict(times)
        for i in range(pointNumber):
            print(times[i][0])
        for i in range(10):
            print("0")
        for i in range(pointNumber):
            print(prices[i][0])
        return regressor.coef_[0][0]

    """ Fit simple parabola """
    def fitParabola(self, ticker, pointNumber):
        feed = ticker.getTickerFeed()
        times = ticker.getTimeFeed()
        if pointNumber > len(feed):
            pointNumber = len(feed)

        feed = feed[-pointNumber:]
        times = times[-pointNumber:]
        prices = []
        for i in range(pointNumber):
            print("accessing point: " + str(i))
            prices.append(float(feed[i]["price"]))
            times[i] = float(times[i])

        # Pull the times back to x=0 so we can know what happens next
        latestTime = times[-1]
        for i in range(len(prices)):
            times[i] = times[i] - latestTime
        for i in range(len(times)):
            print((times[i]))
        for i in range(len(prices)):
            print((prices[i]))


        return numpy.polyfit(times, prices, 2, full=True)