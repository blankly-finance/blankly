"""
    Formatting for platform backtest result
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

import uuid


def __dict_from_df_dict(dict_of_df: dict) -> dict:
    """
    This creates a serializable dictionary from a dictionary with pandas df:
    {
        'AAPL': df.DataFrame
        'MSFT': df.DataFrame
    }
    ->
    {
        'AAPL': df.DataFrame.to_dict()
        'MSFT': df.DataFrame.to_dict()
    }
    The function does not check for nested dataframes

    :arg dict_of_df: A dictionary with dataframes as values of the internal keys
    :return: dict
    """
    output_dict = {}
    for i in list(dict_of_df.keys()):
        output_dict[i] = dict_of_df[i].to_dict()

    return output_dict


def __compress_dict_series(values_column: dict, time_dictionary: dict):
    """
    Remove duplicate keys from the account value or anything that is associated with a time series

    :param values_column: A dictionary with index as key and any sort of value
    :param time_dictionary: A dictionary with index also as key but a time that corresponds to the same index in the
        values column
    :return: None
    """
    values_keys = list(values_column.keys())
    time_keys = list(time_dictionary.keys())

    # Check to see if the dictionaries are longer than 0
    if len(values_keys) == 0:
        return {}

    last_value = values_column[values_keys[0]]
    output_dict = {
        time_dictionary[time_keys[0]]: last_value
    }
    for i in range(len(values_column)):
        if last_value != values_column[values_keys[i]]:
            output_dict[time_dictionary[time_keys[i]]] = values_column[values_keys[i]]

            last_value = values_column[values_keys[i]]

    return output_dict


def __parse_backtest_trades(trades: list, limit_executed: list, limit_canceled: list, market_executed: list):
    """
    Determine the lifecycle of limit orders

    :param trades: The list of trades from the backtest
    :param limit_executed: The list of limit orders that were executed
    :param limit_canceled: The list of limit orders that were canceled
    :param market_executed: The list of executed market orders
    :return: None
    """

    # Now just parse if there should be an executed time or a canceled time
    for i in range(len(trades)):
        trades[i]['time'] = trades[i].pop('created_at')
        if trades[i]['type'] == 'limit':
            # TODO this wastes a few CPU cycles at the moment so it could be cleaned up
            for j in limit_executed:
                if trades[i]['id'] == j['id']:
                    trades[i]['time'] = j['executed_time']
                    trades[i]['price'] = trades[i]['price']
                    break

            for j in limit_canceled:
                if trades[i]['id'] == j['id']:
                    trades[i]['canceledTime'] = j['canceled_time']
                    break
        elif trades[i]['type'] == 'market':
            # This adds in the execution price for the market orders
            trades[i]['type'] = 'spot-market'
            for j in market_executed:
                if trades[i]['id'] == j['id']:
                    trades[i]['price'] = j['executed_price']
                    break

    return trades


def format_metric(metrics: dict, display_name, type_: str):
    return {
        "value": metrics[display_name],
        "display_name": display_name,
        "type": type_
    }


def format_platform_result(backtest_result):
    """
    Export the finished backtest result

    Args:
        backtest_result: A BacktestResult object to export
    """
    # We're given a dictionary of dataframes and that has to be transformed to a dictionary of dictionaries
    history_and_returns = __dict_from_df_dict(backtest_result.history_and_returns)

    # Grab a list of the traded assets
    # The paper trade interface format may change in the future to be more optimized
    traded_symbols = []
    for i in backtest_result.trades['created']:
        if i['symbol'] not in traded_symbols:
            traded_symbols.append(i['symbol'])

    # Set the account values to None
    raw_or_resampled_account_values = None

    # Now we can show the price events resolution and their symbol by knowing the order in the array they appear
    #  in
    price_events = []
    if len(backtest_result.price_events) > 0:
        shortest_price_event = backtest_result.price_events[0]['interval']
        for i in backtest_result.price_events:
            if i['interval'] < shortest_price_event:
                shortest_price_event = i['interval']
            price_events.append({'symbol': i['asset_id'], 'interval': i['interval'], 'ohlcv': i['ohlc']})

        if shortest_price_event < 3600:
            # Turn raw account values
            raw_or_resampled_account_values = backtest_result.resample_account('Account Value ('
                                                                               + backtest_result.quote_currency +
                                                                               ')', 3600).to_dict()

    # Now grab the account value dictionary itself
    # Now just replicate the format of the resampled version
    # This was the annoying backtest glitch that almost cost us an investor meeting so its important
    if raw_or_resampled_account_values is None:
        history = history_and_returns['history']
        account_value_name = 'Account Value (' + backtest_result.quote_currency + ')'
        raw_or_resampled_account_values = {
            'value': history[account_value_name],
            'time': history['time']
        }

    # Now grab the raw account values
    compressed_asset_column = __compress_dict_series(raw_or_resampled_account_values['value'],
                                                     raw_or_resampled_account_values['time'])

    compressed_array_conversion = []
    for i in compressed_asset_column:
        compressed_array_conversion.append({
            'time': i,
            'value': compressed_asset_column[i]
        })

    compressed_asset_keys = list(compressed_asset_column.keys())
    first_account_value = compressed_asset_column[compressed_asset_keys[0]]
    last_account_value = compressed_asset_column[compressed_asset_keys[-1]]

    trades = __parse_backtest_trades(backtest_result.trades['created'],
                                     backtest_result.trades['limits_executed'],
                                     backtest_result.trades['limits_canceled'],
                                     backtest_result.trades['executed_market_orders'])

    # Now change the metrics keys to be nicer
    metrics = backtest_result.metrics
    refined_metrics = {
        'calmar': format_metric(metrics, 'Calmar Ratio', 'number'),
        'cagr': format_metric(metrics, 'Compound Annual Growth Rate (%)', 'number'),
        'cavr': format_metric(metrics, 'Conditional Value-at-Risk', 'number'),

        'cum_returns': format_metric(metrics, 'Cumulative Returns (%)', 'number'),
        'max_drawdown': format_metric(metrics, 'Max Drawdown (%)', 'number'),
        'resampled_time': format_metric(metrics, 'Resampled Time', 'number'),

        'risk_free_rate': format_metric(metrics, 'Risk Free Return Rate', 'number'),
        'sharpe': format_metric(metrics, 'Sharpe Ratio', 'number'),
        'sortino': format_metric(metrics, 'Sortino Ratio', 'number'),

        'value_at_risk': format_metric(metrics, 'Value-at-Risk', 'number'),
        'variance': format_metric(metrics, 'Variance (%)', 'number'),
        'volatility': format_metric(metrics, 'Volatility', 'number')
    }

    backtest_result.metrics = refined_metrics
    return {
        'symbols': traded_symbols,
        'quote_asset': backtest_result.quote_currency,
        'start_time': backtest_result.start_time,
        'stop_time': backtest_result.stop_time,
        'account_values': compressed_array_conversion,
        'trades': trades,
        'metrics': refined_metrics,
        'indicators': {},  # Add to this array when we support
        # strategy indicators
        'price_events': price_events,
        'user_callbacks': backtest_result.user_callbacks,
        'initial_account_value': first_account_value,
        'final_account_value': last_account_value,
        'backtest_id': str(uuid.uuid4())
        # Everything above here is put into the firebase root
    }
