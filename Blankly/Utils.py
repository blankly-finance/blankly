import json, numpy, time
from sklearn.linear_model import LinearRegression
import iso8601


class Utils:
    def __init__(self):
        pass

    """ 
    Json pretty printer for show arguments
    """
    def printJSON(self, jsonObject):
        print(self.returnPrettyJSON(jsonObject))

    """ 
    Json pretty printer for general string usage
    """
    def returnPrettyJSON(self, jsonObject):
        out = json.dumps(jsonObject.json(), indent=2)
        return out

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
