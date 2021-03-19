import Blankly.Local_Account.LocalAccount as Local_Account
import Blankly.Constants as Constants


def tradeLocal(buy_or_sell, currency, crypto_amount_exchanged, ticker):
    if buy_or_sell == "sell":
        # You only get in USD the amount after fees though
        Local_Account.account["USD"] = Local_Account.account["USD"] + (
                float(ticker.get_most_recent_tick()["price"]) * crypto_amount_exchanged * (
                1 - Constants.PRETEND_FEE_RATE))
        # When you sell you get all crypto deducted
        Local_Account.account[currency] = Local_Account.account[currency] - crypto_amount_exchanged
    else:
        # Used for resetting USD value if we drop negative
        previous_account_value = Local_Account.account["USD"]
        # When you buy you get the full crypto amount, but more deducted in usd
        Local_Account.account["USD"] = Local_Account.account["USD"] - (
                Constants.PRETEND_FEE_RATE * crypto_amount_exchanged + crypto_amount_exchanged) * float(
            ticker.get_most_recent_tick()["price"])
        if Local_Account.account["USD"] < 0:
            Local_Account.account["USD"] = previous_account_value
            raise Exception("Insufficient funds")

        # And the after fees amount added to crypto
        Local_Account.account[currency] = Local_Account.account[currency] + crypto_amount_exchanged
