import LocalAccount
import Constants

def tradeLocal(buyOrSell, currency, cryptoAmountExchanged, ticker):
    if buyOrSell == "sell":
        # You only get in USD the amount after fees though
        LocalAccount.account["USD"] = LocalAccount.account["USD"] + (
                    float(ticker.getMostRecentTick()["price"]) * cryptoAmountExchanged * (
                        1 - Constants.PRETEND_FEE_RATE))
        # When you sell you get all crypto deducted
        LocalAccount.account[currency] = LocalAccount.account[currency] - cryptoAmountExchanged

    else:
        # Used for resetting USD value if we drop negative
        previousAccountValue = LocalAccount.account["USD"]
        # When you buy you get the full crypto amount, but more deducted in usd
        LocalAccount.account["USD"] = LocalAccount.account["USD"] - (
                    Constants.PRETEND_FEE_RATE * cryptoAmountExchanged + cryptoAmountExchanged) * float(
            ticker.getMostRecentTick()["price"])
        if LocalAccount.account["USD"] < 0:
            LocalAccount.account["USD"] = previousAccountValue
            raise Exception("Insufficient funds")

        # And the after fees amount added to crypto
        LocalAccount.account[currency] = LocalAccount.account[currency] + cryptoAmountExchanged