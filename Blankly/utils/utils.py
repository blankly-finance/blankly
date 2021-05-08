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

import datetime as DT
import dateutil.parser as DP
import json
import numpy
import warnings

from sklearn.linear_model import LinearRegression


# Recursively check if the user has all the preferences, inform when defaults are missing
def __compare_dicts(default_settings, user_settings):
    for k, v in default_settings.items():
        if isinstance(v, dict):
            if k in user_settings:
                __compare_dicts(v, user_settings[k])
            else:
                warning_string = "\"" + str(k) + "\" not specified in preferences, defaulting to: \"" + str(v) + \
                                 "\""
                warnings.warn(warning_string)
                user_settings[k] = v
        else:
            if k in user_settings:
                continue
            else:
                warning_string = "\"" + str(k) + "\" not specified in preferences, defaulting to: \"" + str(v) + \
                                 "\""
                warnings.warn(warning_string)
                user_settings[k] = v
    return user_settings


settings_cache = None

default_settings = {
    "settings": {
        "account_update_time": 5000,
        "paper_trade": True,
        "use_sandbox": False,
        "binance_tld": "us",
        "websocket_buffer_size": 100000,
    }
}


def load_user_preferences(override_path=None):
    global settings_cache
    if settings_cache is None:
        try:
            if override_path is None:
                f = open("Settings.json", )
                preferences = json.load(f)
            else:
                f = open(override_path, )
                preferences = json.load(f)
        except FileNotFoundError as e:
            raise FileNotFoundError("Make sure a Settings.json file is placed in the same folder as the project "
                                    "working directory!")
        preferences = __compare_dicts(default_settings, preferences)
        settings_cache = preferences
        return preferences
    else:
        return settings_cache


def pretty_print_JSON(json_object):
    """
    Json pretty printer for general string usage
    """
    out = json.dumps(json_object, indent=2)
    print(out)
    return out


def epoch_from_ISO8601(ISO8601):
    return DP.parse(ISO8601).timestamp()


def ISO8601_from_epoch(epoch):
    return DT.datetime.utcfromtimestamp(epoch).isoformat() + 'Z'


def get_price_derivative(ticker, point_number):
    """
    Performs regression n points back
    """
    feed = numpy.array(ticker.get_ticker_feed()).reshape(-1, 1)
    times = numpy.array(ticker.get_time_feed()).reshape(-1, 1)
    if point_number > len(feed):
        point_number = len(feed)

    feed = feed[-point_number:]
    times = times[-point_number:]
    prices = []
    for i in range(point_number):
        prices.append(feed[i][0]["price"])
    prices = numpy.array(prices).reshape(-1, 1)

    regressor = LinearRegression()
    regressor.fit(times, prices)
    regressor.predict(times)
    return regressor.coef_[0][0]


def fit_parabola(ticker, point_number):
    """
    Fit simple parabola
    """
    feed = ticker.get_ticker_feed()
    times = ticker.get_time_feed()
    if point_number > len(feed):
        point_number = len(feed)

    feed = feed[-point_number:]
    times = times[-point_number:]
    prices = []
    for i in range(point_number):
        prices.append(float(feed[i]["price"]))
        times[i] = float(times[i])

    # Pull the times back to x=0 so we can know what happens next
    latest_time = times[-1]
    for i in range(len(prices)):
        times[i] = times[i] - latest_time

    return numpy.polyfit(times, prices, 2, full=True)


def to_blankly_coin_id(coin_id, exchange, base_currency):
    if exchange == "binance":
        index = int(coin_id.find(base_currency))
        coin_id = coin_id[0:index]
        return coin_id + "-" + base_currency
    if exchange == "coinbase_pro":
        return coin_id


def to_exchange_coin_id(blankly_coin_id, exchange):
    if exchange == "binance":
        return blankly_coin_id.replace('-', '')
    if exchange == "coinbase_pro":
        return blankly_coin_id


def get_base_currency(blankly_coin_id):
    # Gets the BTC of the BTC-USD
    return blankly_coin_id.split('-')[0]


def get_quote_currency(blankly_coin_id):
    # Gets the USD of the BTC-USD
    return blankly_coin_id.split('-')[1]


def rename_to(keys_array, renaming_dictionary):
    """
    Args:
        keys_array: A two dimensional array that contains information on which keys are changed:
            keys_array = [
                ["key1", "new name"],
                ["id", "user_id"],
                ["frankie", "gerald"],
            ]
        renaming_dictionary: Dictionary to perform the renaming on
    """
    renaming_dictionary["exchange_specific"] = {}
    for i in keys_array:
        try:
            # Check if it has the new name
            error_test = renaming_dictionary[i[1]]
            # If we're here this key has already been defined, push it to the specific
            renaming_dictionary["exchange_specific"][i[1]] = renaming_dictionary.pop(i[1])
        except KeyError:
            pass
        renaming_dictionary[i[1]] = renaming_dictionary.pop(i[0])
    return renaming_dictionary


# Non-recursive check
def isolate_specific(needed, compare_dictionary):
    """
    This is the parsing algorithm used to homogenize the dictionaries
    """
    # Create a column vector for the keys
    column = [column[0] for column in needed]
    # Create an area to hold the specific data
    exchange_specific = {}
    required = False
    for k, v in compare_dictionary.items():
        # Check if the value is one of the keys
        for index, val in enumerate(column):
            required = False
            # If it is, there is a state value for it
            if k == val:
                # Push type to value
                compare_dictionary[k] = needed[index][1](v)
                required = True
                break
        # Must not be found
        # Append non-necessary to the exchange specific dict
        # There has to be a way to do this without raising a flag value
        if not required:
            exchange_specific[k] = compare_dictionary[k]

    # If there exists the exchange specific dict in the compare dictionary
    # This is done because after renaming, if there are naming conflicts they will already have been pushed here,
    # generally the "else" should always be what runs.
    if "exchange_specific" not in compare_dictionary:
        # If there isn't, just add it directly
        compare_dictionary["exchange_specific"] = exchange_specific
    else:
        # If there is, pull them together
        compare_dictionary["exchange_specific"] = {**compare_dictionary["exchange_specific"], **exchange_specific}

        # The tag could be in the exchange_specific tag, meaning the actual tag will get deleted later, pull it out
        if "exchange_specific" in exchange_specific:
            del exchange_specific["exchange_specific"]
    # Pull the specific keys out
    for k, v in exchange_specific.items():
        del compare_dictionary[k]
    return compare_dictionary
