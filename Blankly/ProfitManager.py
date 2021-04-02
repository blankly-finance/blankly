"""
    Risk management or purchase management for recent buys.
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

import Constants


class ProfitManager:
    def __init__(self, currencyType, ticker, exchanges=None, show=False):
        if exchanges is None:
            exchanges = []
        self.__currencyType = currencyType
        self.__exchanges = exchanges
        self.__ticker = ticker
        ticker.append_callback(self)
        self.__show = show

    def addExchange(self, exchange):
        self.__exchanges.append(exchange)

    def getExchange(self, index):
        return self.__exchanges[index]

    """ This will fire when the attached ticker receives a new price update """

    def priceEvent(self, tick):
        print("Tick")
        price = float(tick["price"])
        for i in range(len(self.__exchanges)):
            if (self.__exchanges[i].getIfSold() is True):
                # If this one is sold, just forget about it
                # TODO move this remove to the sell areas. This isn't done yet because it isn't nailed down
                del self.__exchanges[i]
                continue
            profitable = self.__exchanges[i].is_profitable()
            # This makes sure there is some degree of profitability
            profitableSellPrice = self.__exchanges[i].is_profitable_buy()
            # If the current price is higher than the exchange's minimum to be considered sellable
            if self.__show:
                print(str(price) + " needs to get past: " + str(
                    profitableSellPrice + (profitableSellPrice * Constants.SELL_MIN)))
                print("Minimum to surpass fees: " + str(profitableSellPrice))

            if price > profitableSellPrice + (profitableSellPrice * Constants.SELL_MIN):
                # Set allow it to be up for selling
                self.__exchanges[i].setIfPastSellMin(True)
                print("Exchange " + str(self.__exchanges[i].get_purchase_id()) + " is now past sell min")

            # Now check if the price has dropped from the sell min to almost loosing profit
            """ 
            This way of making sure it has to go past a minimum allows it to keep rising past 
                                                        to emergency sell it has to be less than profitable, then less than the minimum sellable price minus half of that difference. This puts a buffer in that ensures slight price deviations won't mean it gets sold 
            """
            if self.__exchanges[i].getIfPastSellMin() and (profitableSellPrice < price < (
                    (profitableSellPrice + (profitableSellPrice * Constants.SELL_MIN)) - (
                    (profitableSellPrice + (profitableSellPrice * Constants.SELL_MIN)) - profitableSellPrice) / 2)):
                self.__exchanges[i].sellSelf()
                print("Emergency selling self: " + str(self.__exchanges[i].get_purchase_id()))
                print("Now have: " + str(LocalAccount.account["USD"]) + " USD")
                print("and: " + str(LocalAccount.account["BTC-USD"]) + " BTC")
            elif (profitableSellPrice < price < ((profitableSellPrice + (profitableSellPrice * Constants.SELL_MIN)) - ((
                                                                                                                               profitableSellPrice + (
                                                                                                                               profitableSellPrice * Constants.SELL_MIN)) - profitableSellPrice) / 2)) and (
            not self.__exchanges[i].getIfPastSellMin()):
                # Sell even if it hasn't gone very high and the price is looking down
                if self.__utils.get_price_derivative(self.__ticker, Constants.EMERGENCY_SELL_SAMPLE) < 0:
                    print("Emergency selling self because market is trending downwards: " + str(
                        self.__exchanges[i].get_purchase_id()))
                    self.__exchanges[i].sellSelf()

            elif not profitable:
                if self.__show:
                    print("Exchange " + str(self.__exchanges[i].get_purchase_id()) + " is not profitable")
