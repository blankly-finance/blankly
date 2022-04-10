"""
    Updated CLI for interacting with and uploading blankly models.
    Copyright (C) 2022 Matias Kotlik

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

import argparse
import json
import os.path
import sys
import traceback
import webbrowser
from pathlib import Path
from typing import Optional
import pkgutil

from questionary import Choice

from blankly.deployment.api import API, blankly_deployment_url
from blankly.deployment.deploy import zip_dir, get_python_version
from blankly.deployment.keys import add_key, load_keys, write_keys
from blankly.deployment.login import logout, poll_login, get_token
from blankly.deployment.ui import text, confirm, print_work, print_failure, print_success, select, show_spinner
from blankly.deployment.exchange_data import EXCHANGES, Exchange, EXCHANGE_CHOICES, exc_display_name, \
    EXCHANGE_CHOICES_NO_KEYLESS

TEMPLATES = {'strategy': {'none': 'none.py',
                          'rsi_bot': 'rsi_bot.py'},
             'screener': {'none': 'none_screener.py',
                          'rsi_screener': 'rsi_screener.py'}}

AUTH_URL = 'https://app.blankly.finance/auth/signin?redirectUrl=/deploy'


def validate_non_empty(text):
    if not text.strip():
        return 'Please enter a value'
    return True


def create_model(api, name, description, model_type, project_id=None):
    with show_spinner('Creating model') as spinner:
        try:
            model = api.create_model(project_id or api.user_id, model_type, name, description)
        except Exception:
            spinner.fail('Failed to create model')
            raise
        spinner.ok('Created model')
    return model


def ensure_login() -> API:
    # TODO print selected team ?
    api = is_logged_in()
    if api:
        return api
    return launch_login_flow()


def is_logged_in() -> Optional[API]:
    token = get_token()
    if not token:
        return

    # log into deployment api
    try:
        return API(token)
    except Exception:  # TODO
        return


def launch_login_flow() -> API:
    try:
        webbrowser.open_new(AUTH_URL)
        print_work(f'Your browser was opened to {AUTH_URL}. Open the window and login.')
    except Exception:
        print_work(f'Could not find a browser to open. Navigate to {AUTH_URL} and login')

    api = None
    with show_spinner(f'Waiting for login') as spinner:
        try:
            api = poll_login()
        except Exception:
            pass  # we just check for api being valid, poll_login can return None

        if not api:
            spinner.fail('Failed to login')
            sys.exit(1)

        spinner.ok('Logged in')
    return api


def add_key_interactive(exchange: Exchange):
    tld = None
    if exchange.tlds:
        tld = select('What TLD are you using?',
                     [Choice(f'{exchange.name}.{tld}', tld) for tld in exchange.tlds]).unsafe_ask()

    name = text('Give this key a name:', instruction='(Optional)').unsafe_ask()

    saved_data = {}
    for instruction, key in exchange.key_info.items():
        saved_data[key] = text(f'{instruction}:', validate=validate_non_empty).unsafe_ask().strip()
    saved_data['sandbox'] = confirm('Is this testnet/sandbox key?', default=False).unsafe_ask()

    if add_key(exchange, tld, name, saved_data):
        print_success(f'Your API key for {exchange.display_name} was added to this model')
        return tld
    print_failure(f'Your API Key for {exchange.display_name} was not added to the model')
    return False


def blankly_init(args):
    # warn nonempty dir
    dir_is_empty = len([f for f in os.listdir() if not f.startswith('.')]) == 0
    if not dir_is_empty \
            and not confirm('This directory is not empty. Would you like to continue anyways?').unsafe_ask():
        return

    exchange = select('What exchange would you like to connect to?', EXCHANGE_CHOICES).unsafe_ask()

    model_type = 'strategy'
    tld = None
    template = None
    if exchange:
        model_type = select('What type of model do you want to create?',
                            [Choice(mt.title(), mt) for mt in TEMPLATES]).unsafe_ask()
        templates = TEMPLATES[model_type]

        template_name = select('What template would you like to use for your new model?', templates).unsafe_ask()
        template = templates[template_name]

        if confirm('Would you like to add keys for this exchange?\n'
                   'You can do this later at any time by running `blankly key add`').unsafe_ask():
            tld = add_key_interactive(exchange)

    model = None
    if args.prompt_login and confirm('Would you like to connect this model to the Blankly Platform?').unsafe_ask():
        api = ensure_login()
        model = get_model_interactive(api, model_type)

    with show_spinner('Generating files') as spinner:
        files = [
            ('bot.py', generate_bot_py(exchange, template), False),
            ('backtest.json', generate_backtest_json(exchange), False),
            ('requirements.txt', 'blankly\n', False),
            ('keys.json', generate_keys_json(), True),
            ('blankly.json', generate_blankly_json(model, model_type), False),
            ('settings.json', generate_settings_json(tld or 'com'), False)
        ]
        spinner.ok('Generated files')

    for path, data, force_overwrite in files:
        exists = Path(path).exists()
        overwrite_prompt = confirm(f'{path} already exists, would you like to overwrite it?', default=False)
        if force_overwrite or not exists or overwrite_prompt.unsafe_ask():
            with open(path, 'w') as file:
                file.write(data)

    # TODO open on platform WITHOUT STARTING

    print_success('Done! Your model was created. Run `python bot.py` to run a backtest and get started.')


def get_model_interactive(api, model_type):
    create = select('Would you like to create a new model or attach to an existing one?',
                    [Choice('Create new model', True), Choice('Attach to existing model', False)]).unsafe_ask()
    if create:
        default_name = Path.cwd().name  # default name is working dir name
        name = text('Model name?', default=default_name, validate=validate_non_empty).unsafe_ask()
        description = text('Model description?', instruction='(Optional)').unsafe_ask()
        teams = api.list_teams()
        team_id = None
        if teams:
            team_choices = [Choice('Create on my personal account', False)] \
                           + [Choice(team.get('name', team['id']), team['id']) for team in teams]
            team_id = select('What team would you like to create this model under?', team_choices).unsafe_ask()
            return create_model(api, name, description, model_type, team_id or None)

    with show_spinner('Loading models...') as spinner:
        models = api.list_all_models()
        spinner.ok('Loaded')

    model = select('Select an existing model to attach to:',
                   [Choice(get_model_repr(model), model) for model in models]).unsafe_ask()
    if model.get('type', None) != model_type:
        pass  # TODO
    return model


def get_model_repr(model: dict) -> str:
    name = model.get('name', model['id'])
    team = model.get('team', {}).get('name', None)
    if team:
        name = team + ' - ' + name
    return name


def generate_settings_json(tld: str):
    data = {"settings": {"use_sandbox_websockets": False,
                         "websocket_buffer_size": 10000,
                         "test_connectivity_on_auth": True,
                         "coinbase_pro": {"cash": "USD"},
                         "binance": {"cash": "USDT",
                                     "binance_tld": tld, },
                         "alpaca": {"websocket_stream": "iex",
                                    "cash": "USD",
                                    "enable_shorting": True,
                                    "use_yfinance": False},
                         "oanda": {"cash": "USD"},
                         "keyless": {"cash": "USD"},
                         "ftx": {"cash": "USD",
                                 "ftx_tld": tld, },
                         "ftx_futures": {"cash": "USD",
                                         "ftx_tld": tld},
                         "kucoin": {"cash": "USDT"}}}
    return json.dumps(data, indent=4)


def generate_keys_json():
    try:
        with open('keys.json') as file:
            keys = json.load(file)
    except FileNotFoundError:
        keys = {}

    for exchange in EXCHANGES:
        keys[exchange.name] = keys.get(exchange.name, {
            'example-portfolio': {v: '*' * 20 for v in exchange.key_info.values()}
        })
        for portfolio in keys[exchange.name].values():
            portfolio['sandbox'] = portfolio.get('sandbox', False)
    return json.dumps(keys, indent=4)


def generate_blankly_json(model: Optional[dict], model_type):
    data = {'main_script': './bot.py',
            'python_version': get_python_version(),
            'requirements': './requirements.txt',
            'working_directory': '.',
            'ignore_files': ['price_caches', '.git', '.idea', '.vscode'],
            'backtest_args': {'to': '1y'},
            'type': model_type,
            'screener': {'schedule': '30 14 * * 1-5'}}
    if model:
        data['model_id'] = model['id']
        data['project_id'] = model['projectId']
    return json.dumps(data, indent=4)


def generate_backtest_json(exchange: Optional[Exchange]) -> str:
    currency = exchange.currency if exchange else 'USD'
    data = {'price_data': {'assets': []},
            'settings': {'use_price': 'close',
                         'smooth_prices': False,
                         'GUI_output': True,
                         'show_tickers_with_zero_delta': False,
                         'save_initial_account_value': True,
                         'show_progress_during_backtest': True,
                         'cache_location': './price_caches',
                         'continuous_caching': True,
                         'resample_account_value_for_metrics': '1d',
                         'quote_account_value_in': currency,
                         'ignore_user_exceptions': True,
                         'risk_free_return_rate': 0.0,
                         'benchmark_symbol': None}}
    return json.dumps(data, indent=4)


def generate_bot_py(exchange: Optional[Exchange], template: str) -> str:
    if not exchange:
        # template should be None
        return pkgutil.get_data('blankly', 'data/templates/keyless.py').decode('utf-8')
    bot_py = pkgutil.get_data('blankly', f'data/templates/{template}').decode('utf-8')
    for pattern, replacement in [
        ('EXCHANGE_NAME', exchange.display_name,),
        ('EXCHANGE_CLASS', exchange.python_class,),
        ('SYMBOL_LIST', "['" + "', '".join(exchange.symbols) + "']",),
        ('SYMBOL', exchange.symbols[0],)
    ]:
        bot_py = bot_py.replace(pattern, replacement)
    return bot_py


def blankly_login(args):
    if is_logged_in():
        print_success('You are already logged in')
        return

    launch_login_flow()


def blankly_logout(args):
    with show_spinner('Logging out of the Blankly Platform') as spinner:
        try:
            logout()
        except Exception:
            spinner.fail('Failed to logout')
            raise
        spinner.ok('Logged out')


def ensure_model(api: API):
    # create model if it doesn't exist
    try:
        with open('blankly.json', 'r') as file:
            data = json.load(file)
    except FileNotFoundError:
        print_failure('There was no model detected in this directory. Try running `blankly init` to create one')
        sys.exit(1)

    if 'plan' not in data:
        data['plan'] = select('Select a plan:', [Choice(f'{name} - CPU: {info["cpu"]} RAM: {info["ram"]}', name)
                                                 for name, info in api.get_plans('live').items()]).unsafe_ask()

    if 'model_id' not in data or 'project_id' not in data:
        model = get_model_interactive(api, data['type'])
        data['model_id'] = model['modelId']
        data['project_id'] = model['projectId']

    # save model_id and plan back into blankly.json
    with open('blankly.json', 'w') as file:
        json.dump(data, file, indent=4)

    return data


def missing_deployment_files() -> list:
    paths = ['bot.py', 'blankly.json', 'keys.json', 'backtest.json', 'requirements.txt', 'settings.json']
    return [path for path in paths if not Path(path).is_file()]


def blankly_deploy(args):
    api = ensure_login()

    data = ensure_model(api)
    for path in missing_deployment_files():
        if not confirm(f'{path} is missing. Are you sure you want to continue?',
                       default=False).unsafe_ask():
            print_failure('Deployment cancelled')
            print_failure(f'You can try `blankly init` to regenerate the {path} file.')
            return

    description = text('Enter a description for this version of the model:').unsafe_ask()

    with show_spinner('Uploading model') as spinner:
        model_path = zip_dir('.', data['ignore_files'])

        params = {
            'file_path': model_path,
            'project_id': data['project_id'],  # set by ensure_model
            'model_id': data['model_id'],  # set by ensure_model
            'version_description': description,
            'python_version': get_python_version(),
            'type_': data.get('type', 'strategy'),
            'plan': data['plan']  # set by ensure_model
        }
        if data['type'] == 'screener':
            params['schedule'] = data['screener']['schedule']

        response = api.deploy(**params)
        if response.get('status', None) == 'success':
            spinner.ok('Model uploaded')
        else:
            spinner.fail('Error: ' + response['error'])


def blankly_add_key(args):
    exchange = select('What exchange would you like to add a key for?', EXCHANGE_CHOICES_NO_KEYLESS).unsafe_ask()
    add_key_interactive(exchange)


def blankly_list_key(args):
    data = load_keys()
    for exchange_name, keys in data.items():
        for name, key_data in keys.items():
            # filter 'empty'
            if any((isinstance(d, str) and '*' in d) for d in key_data.values()):
                continue
            exchange_display_name = exc_display_name(exchange_name)
            print_work(f'{exchange_display_name}: {name}')
            for k, v in key_data.items():
                print_work(f'    {k}: {v}')


def blankly_remove_key(args):
    data = load_keys()

    key_choices = [Choice(f'{exc_display_name(exchange)}: {name}', (exchange, name))
                   for exchange, keys in data.items() for name in keys]
    if not key_choices:
        return
    exchange, key = select('Which key would you like to delete?', key_choices).unsafe_ask()

    del data[exchange][key]
    write_keys(data)


def blankly_key(args):
    func = select('What would you like to do?', [
        Choice('Add a key', blankly_add_key),
        Choice('Show all keys', blankly_list_key),
        Choice('Remove a key', blankly_remove_key)
    ]).unsafe_ask()
    func(args)


def main():
    parser = argparse.ArgumentParser(description='Blankly CLI & deployment tool')
    subparsers = parser.add_subparsers(required=True)

    init_parser = subparsers.add_parser('init', help='Initialize a new model in the current directory')
    init_parser.add_argument('-n', '--no-login', action='store_false', dest='prompt_login',
                             help='don\'t prompt to connect to Blankly Platform')
    init_parser.set_defaults(func=blankly_init)

    login_parser = subparsers.add_parser('login', help='Login to the Blankly Platform')
    login_parser.set_defaults(func=blankly_login)

    logout_parser = subparsers.add_parser('logout', help='Logout of the Blankly Platform')
    logout_parser.set_defaults(func=blankly_logout)

    deploy_parser = subparsers.add_parser('deploy', help='Upload this model to the Blankly Platform')
    deploy_parser.set_defaults(func=blankly_deploy)

    key_parser = subparsers.add_parser('key', help='Manage model Exchange API keys')
    key_parser.set_defaults(func=blankly_key)
    key_subparsers = key_parser.add_subparsers()

    key_add_parser = key_subparsers.add_parser('remove', help='Delete API Keys from this model')
    key_add_parser.set_defaults(func=blankly_remove_key)

    key_add_parser = key_subparsers.add_parser('list', help='List API Keys that this model is using')
    key_add_parser.set_defaults(func=blankly_list_key)

    key_add_parser = key_subparsers.add_parser('add', help='Add an API Key to this model')
    key_add_parser.set_defaults(func=blankly_add_key)

    # run the selected command
    args = parser.parse_args()
    try:
        args.func(args)
    except KeyboardInterrupt:
        print_failure('Cancelled by user')
    except Exception:
        print_failure('An error occurred. Traceback:')
        traceback.print_exc()


if __name__ == '__main__':
    main()
