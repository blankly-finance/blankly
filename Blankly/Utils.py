"""
    Utils file for assisting with trades or market analysis.
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


import json, numpy, time
from sklearn.linear_model import LinearRegression
import iso8601
import datetime as DT


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

    def epoch_from_ISO8601(self, ISO8601):
        return time.mktime(iso8601.parse_date(ISO8601).timetuple())

    def ISO8601_from_epoch(self, epoch):
        return DT.datetime.utcfromtimestamp(epoch).isoformat() + 'Z'


    """
    Performs regression n points back
    """
    def getPriceDerivative(self, ticker, pointNumber):
        feed = numpy.array(ticker.get_ticker_feed()).reshape(-1, 1)
        times = numpy.array(ticker.get_time_feed()).reshape(-1, 1)
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
        feed = ticker.get_ticker_feed()
        times = ticker.get_time_feed()
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
