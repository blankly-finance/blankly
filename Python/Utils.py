import json, numpy, time, LocalAccount, Constants
from sklearn.linear_model import LinearRegression
import iso8601



class Utils:
    @staticmethod
    def tradeLocal(buyOrSell, currency, cryptoAmountExchanged, ticker):
        if buyOrSell == "sell":
            # You only get in USD the amount after fees though
            LocalAccount.account["USD"] = LocalAccount.account["USD"] + (float(ticker.getMostRecentTick()["price"]) * cryptoAmountExchanged * (1 - Constants.PRETEND_FEE_RATE))
            # When you sell you get all crypto deducted
            LocalAccount.account[currency] = LocalAccount.account[currency] - cryptoAmountExchanged

        else:
            # When you buy you get the full crypto amount, but more deducted in usd
            LocalAccount.account["USD"] = LocalAccount.account["USD"] - (Constants.PRETEND_FEE_RATE * cryptoAmountExchanged + cryptoAmountExchanged) * float(ticker.getMostRecentTick()["price"])
            # And the after fees amount added to crypto
            LocalAccount.account[currency] = LocalAccount.account[currency] + cryptoAmountExchanged

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
    """
    Order Place Example:
    order = {
        'size': 1.0,
        'price': 1.0,
        'side': 'buy',
        'product_id': 'BTC-USD',
    }
    (size in currency (like .01 BTC), buy/sell (string), product id (BTC-USD))
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
    (size in currency (like .01 BTC), buy/sell (string), product id (BTC-USD))
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
        return regressor.coef_[0][0]

    """ 
    Fit simple parabola 
    """
    def fitParabola(self, ticker, pointNumber):
        feed = ticker.getTickerFeed()
        times = ticker.getTimeFeed()
        if pointNumber > len(feed):
            pointNumber = len(feed)

        feed = feed[-pointNumber:]
        times = times[-pointNumber:]
        prices = []
        for i in range(pointNumber):
            prices.append(float(feed[i]["price"]))
            times[i] = float(times[i])

        # Pull the times back to x=0 so we can know what happens next
        latestTime = times[-1]
        for i in range(len(prices)):
            times[i] = times[i] - latestTime


        return numpy.polyfit(times, prices, 2, full=True)