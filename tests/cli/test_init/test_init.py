import json
import os
import unittest
import shutil
import subprocess


def convert_binance(exchange_name):
    if exchange_name == "binance.us" or exchange_name == "binance.com":
        return 'binance'
    else:
        return exchange_name


def run_cli(commands: list, cwd=f'./tests/cli'):
    my_env = os.environ.copy()
    my_env["PYTHONPATH"] = os.path.abspath('./')

    script_abs = os.path.abspath('./blankly/deployment/cli.py')
    all_commands = ['python', script_abs] + commands
    p = subprocess.Popen(all_commands, cwd=cwd, env=my_env)
    p.wait()


def check_backtest_settings(settings: str, expected_defaults: dict):
    settings = json.loads(settings)
    assert(settings['settings']['quote_account_value_in'] == expected_defaults['quote_currency'])


def check_deploy_settings(settings: str, expected_defaults: dict):
    # Just check if it will serialize
    json.loads(settings)
    assert True


def check_bot_script(bot: str, expected_defaults: dict):
    assert(expected_defaults['exchange'] in bot)


def check_keys_settings(keys: str, expected_defaults: dict):
    keys = json.loads(keys)
    exchange = convert_binance(expected_defaults['exchange_name'])
    assert(exchange in keys)


def check_requirements(requirements: str, expected_defaults: dict):
    assert('blankly' in requirements)


def check_settings(settings: str, expected_defaults: dict):
    settings = json.loads(settings)
    exchange = convert_binance(expected_defaults['exchange_name'])
    if 'tld' in expected_defaults:
        if settings['settings'][exchange][exchange + '_tld'] != expected_defaults['tld']:
            print(f"Incorrect tld found in exchange {settings['exchange_name']}")
            assert False

    assert(settings['settings'][exchange]['cash'] == expected_defaults['quote_currency'])


class TestInit(unittest.TestCase):
    exchanges = ['binance.com', 'binance.us', 'coinbase_pro', 'alpaca', 'ftx', 'oanda', 'kucoin']
    inits_folder = 'generated_inits'
    exchange_defaults = {
        'alpaca': {
            'exchange': 'blankly.Alpaca',
            'quote_currency': 'USD'
        },
        'binance.com': {
            'tld': 'com',
            'exchange': 'blankly.Binance',
            'quote_currency': 'USDT'
        },
        'binance.us': {
            'tld': 'us',
            'exchange': 'blankly.Binance',
            'quote_currency': 'USDT'
        },
        'coinbase_pro': {
            'exchange': 'blankly.CoinbasePro',
            'quote_currency': 'USD'
        },
        'ftx': {
            'exchange': 'blankly.FTX',
            'quote_currency': 'USDT'
        },
        'kucoin': {
            'exchange': 'blankly.Kucoin',
            'quote_currency': 'USDT'
        },
        'oanda': {
            'exchange': 'blankly.Oanda',
            'quote_currency': 'USD'
        }
    }

    @classmethod
    def setUpClass(cls) -> None:
        cls.exchanges = ['binance.com', 'binance.us',
                         'coinbase_pro', 'alpaca', 'ftx', 'oanda', 'kucoin']
        try:
            shutil.rmtree(f'./tests/cli/test_init/{cls.inits_folder}')
        except FileNotFoundError:
            print("No previous test folder found...")
        os.mkdir(f'./tests/cli/test_init/{cls.inits_folder}')
        for i in cls.exchanges:
            os.mkdir(f'./tests/cli/test_init/{cls.inits_folder}/{i}')

    def test_init(self):
        def parse_init_folder(filepath: str, exchange):
            files = ['backtest.json', 'blankly.json', 'bot.py', 'keys.json', 'requirements.txt', 'settings.json']
            evaluators = [check_backtest_settings, check_deploy_settings, check_bot_script, check_keys_settings,
                          check_requirements, check_settings]
            for j in range(len(files)):
                contents = open(filepath + '/' + files[j]).read()

                # Copy the exchange name root into the dict
                defaults_with_root = self.exchange_defaults[exchange]
                defaults_with_root['exchange_name'] = exchange

                # Evaluate here
                evaluators[j](contents, defaults_with_root)

            # This passed
            self.assertTrue(True)

        for i in self.exchanges:
            run_cli(['init', i], cwd=f'./tests/cli/test_init/{self.inits_folder}/{i}')
            parse_init_folder(f'./tests/cli/test_init/{self.inits_folder}/{i}', i)
