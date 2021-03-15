import LocalAccount
import Blankly.Constants as Constants


def tradeLocal(buy_or_sell, currency, crypto_amount_exchanged, ticker):
    if buy_or_sell == "sell":
        # You only get in USD the amount after fees though
        LocalAccount.account["USD"] = LocalAccount.account["USD"] + (
                float(ticker.getMostRecentTick()["price"]) * crypto_amount_exchanged * (
                1 - Constants.PRETEND_FEE_RATE))
        # When you sell you get all crypto deducted
        LocalAccount.account[currency] = LocalAccount.account[currency] - crypto_amount_exchanged
    else:
        # Used for resetting USD value if we drop negative
        previous_account_value = LocalAccount.account["USD"]
        # When you buy you get the full crypto amount, but more deducted in usd
        LocalAccount.account["USD"] = LocalAccount.account["USD"] - (
                Constants.PRETEND_FEE_RATE * crypto_amount_exchanged + crypto_amount_exchanged) * float(
            ticker.getMostRecentTick()["price"])
        if LocalAccount.account["USD"] < 0:
            LocalAccount.account["USD"] = previous_account_value
            raise Exception("Insufficient funds")

        # And the after fees amount added to crypto
        LocalAccount.account[currency] = LocalAccount.account[currency] + crypto_amount_exchanged
