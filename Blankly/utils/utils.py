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
import sys

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
backtest_cache = None

# Copy of settings to compare defaults vs overrides
default_settings = {
    "settings": {
        "account_update_time": 5000,
        "use_sandbox": True,
        "binance_tld": "us",
        "websocket_buffer_size": 100000,
    }
}


def load_json_file(override_path=None):
    f = open(override_path, )
    json_file = json.load(f)
    f.close()
    return json_file


def load_backtest_preferences(override_path=None) -> dict:
    global backtest_cache
    if backtest_cache is None:
        try:
            if override_path is None:
                preferences = load_json_file('backtest.json')
            else:
                preferences = load_json_file(override_path)
        except FileNotFoundError:
            raise FileNotFoundError("To perform a backtest, make sure a backtest.json file is placed in the same "
                                    "folder as the project working directory!")
        # TODO add backtesting preferences compare ability
        # preferences = __compare_dicts(default_settings, preferences)
        backtest_cache = preferences
        return preferences
    else:
        return backtest_cache


def write_backtest_preferences(json_file, override_path=None):
    global backtest_cache
    backtest_cache = json_file
    with open('backtest.json', "w") as preferences:
        preferences.write(json.dumps(json_file, indent=2))


def load_user_preferences(override_path=None) -> dict:
    global settings_cache
    if settings_cache is None:
        try:
            if override_path is None:
                preferences = load_json_file('settings.json')
            else:
                preferences = load_json_file(override_path)
        except FileNotFoundError:
            raise FileNotFoundError("Make sure a settings.json file is placed in the same folder as the project "
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


def to_blankly_coin_id(coin_id, exchange, quote_currency=None) -> str:
    if exchange == "binance":
        if quote_currency is not None:
            index = int(coin_id.find(quote_currency))
            coin_id = coin_id[0:index]
            return coin_id + "-" + quote_currency
        else:
            # Try your best to try to parse anyway
            quotes = ['BNB', 'BTC', 'TRX', 'XRP', 'ETH', 'USDT', 'BUSD', 'AUD', 'BRL', 'EUR', 'GBP', 'RUB',
                      'TRY', 'TUSD', 'USDC', 'PAX', 'BIDR', 'DAI', 'IDRT', 'UAH', 'NGN', 'VAI', 'BVND']
            for i in quotes:
                if __check_ending(coin_id, i):
                    return to_blankly_coin_id(coin_id, 'binance', quote_currency=i)
            raise LookupError("Unable to parse binance coin id of: " + str(coin_id))

    if exchange == "coinbase_pro":
        return coin_id


def __check_ending(full_string, checked_ending) -> bool:
    check_length = len(checked_ending)
    return checked_ending == full_string[-check_length:]


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
    mutated_dictionary = {**renaming_dictionary}
    if "exchange_specific" not in mutated_dictionary:
        mutated_dictionary["exchange_specific"] = {}

    for i in keys_array:
        if i[1] in renaming_dictionary:
            # If we're here this key has already been defined, push it to the specific
            mutated_dictionary["exchange_specific"][i[1]] = renaming_dictionary[i[1]]
            # Then continue with adding the key that we were going to add anyway
        mutated_dictionary[i[1]] = renaming_dictionary[(i[0])]
        del mutated_dictionary[i[0]]
    return mutated_dictionary

# Non-recursive check
def isolate_specific(needed, compare_dictionary):
    """
    This is the parsing algorithm used to homogenize the dictionaries
    """
    # Make a copy of the dictionary so we don't modify it if you loop over
    compare_dictionary = {**compare_dictionary}
    # Create a row vector for the keys
    column = [column[0] for column in needed]    # ex: ['currency', 'available', 'hold']
    # Create an area to hold the specific data
    if 'exchange_specific' in compare_dictionary:
        exchange_specific = compare_dictionary['exchange_specific']
        del compare_dictionary['exchange_specific']
    else:
        exchange_specific = {}

    for k, v in compare_dictionary.items():
        required = False
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

    # Now we need to remove the keys that we appended to exchange_specific
    for k, v in exchange_specific.items():
        del compare_dictionary[k]

    # If there exists the exchange specific dict in the compare dictionary
    # This is done because after renaming, if there are naming conflicts they will already have been pushed here
    # Because we pulled out the naming conflicts dictionary we just just write this directly
    compare_dictionary["exchange_specific"] = exchange_specific

    return compare_dictionary


def convert_epochs(epoch):
    """
    If an epoch time is very long it means that it includes decimals - generally milliseconds. We like the decimal
    format because its unambiguous
    """
    # Hope nobody is fixing this on Friday, June 11, 2128 at 8:53:20 AM (GMT)
    while epoch > 5000000000:
        epoch = epoch / 10
    return epoch


def compare_dictionaries(dict1, dict2) -> bool:
    """
    Compare two output dictionaries to check if they have the same keys (excluding "exchange_specific")
    Args:
        dict1 (dict): First dictionary to compare
        dict2 (dict): Second dictionary to compare
    Returns:
        bool: Are the non specific tags the same?
    """
    if "exchange_specific" not in dict1:
        raise KeyError("Exchange specific tag not in: " + str(dict1))

    if "exchange_specific" not in dict2:
        raise KeyError("Exchange specific tag not in: " + str(dict2))

    # Safely remove keys now
    del dict1["exchange_specific"]
    del dict2["exchange_specific"]

    valid_keys = []

    for key, value in dict1.items():
        # Check to make sure that key is in the other dictionary
        if key in dict2:
            # Now are they the same type
            if not isinstance(dict2[key], type(value)):
                # Issue detected
                print("Type of key " + dict1[key] + " in dict1 is " + str(type(dict1[key])) +
                      ", but is " + str(type(dict2[key])) + " in dict2.")
                return False
            else:
                valid_keys.append(key)
        else:
            # Issue detected
            print(key + " found in dict1 but not in " + str(dict2))
            return False

    # Delete these keys so we can check for differences
    for i in valid_keys:
        del dict1[i]
        del dict2[i]

    if dict1 == {} and dict2 == {}:
        return True
    else:
        print("Differing keys:")
        print(dict1)
        print(dict2)
        return False


def update_progress(progress):
    # update_progress() : Displays or updates a console progress bar
    # Accepts a float between 0 and 1. Any int will be converted to a float.
    # A value under 0 represents a 'halt'.
    # A value at 1 or bigger represents 100%
    bar_length = 10  # Modify this to change the length of the progress bar
    status = ""
    if isinstance(progress, int):
        progress = float(progress)
    if not isinstance(progress, float):
        progress = 0
        status = "error: progress var must be float\r\n"
    if progress < 0:
        progress = 0
        status = "Halt...\r\n"
    if progress >= 1:
        progress = 1
        status = "Done...\r\n"
    block = int(round(bar_length * progress))
    text = "\rProgress: [{0}] {1}% {2}".format("#" * block + "-" * (bar_length - block), round(progress * 100, 2),
                                               status)
    sys.stdout.write(text)
    sys.stdout.flush()


class AttributeDict(dict):
    def __getattr__(self, attr):
        return self[attr]
    def __setattr__(self, attr, value):
        self[attr] = value