import argparse
import sys
import time
import traceback
import webbrowser
from pathlib import Path
from typing import Optional

from yaspin import yaspin

from blankly.deployment.api import API
from blankly.deployment.login import logout, poll_login, get_token
from blankly.deployment.ui import text, confirm, print_work, print_failure, print_success, select, show_spinner

# TODO autogen some of these
EXCHANGES = ['binance.com', 'binance.us', 'coinbase_pro', 'alpaca', 'ftx', 'oanda']

TEMPLATES = ['none', 'rsi_bot']

MODEL_TYPES = ['strategy', 'screener']

AUTH_URL = 'https://app.blankly.finance/auth/signin?redirectUrl=/deploy'


def validate_non_empty(text):
    if not text.strip():
        return 'Please enter a value'
    return True


def get_default_project_id(api) -> str:
    projects = api.list_projects()
    if not projects:
        project = api.create_project('default project', 'default project for all models')
        return str(project['projectId'])
    else:
        return str(projects[0]['id'])


def create_model(api, name, description, model_type):
    with show_spinner('Creating Blankly Platform model') as spinner:
        try:
            model = api.create_model(get_default_project_id(api), model_type, name, description)
        except Exception:
            spinner.fail('Failed to create model')
            raise
        spinner.ok('Created model')
    return model


def ensure_login() -> API:
    api = is_logged_in()
    if api:
        return api
    return poll_login()


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


def blankly_init(args):
    model_type = select('What type of model do you want to create?', [mt.title() for mt in MODEL_TYPES]).unsafe_ask()
    if args.prompt_login and confirm('Would you like to connect this model to the Blankly Platform?').unsafe_ask():
        api = ensure_login()

        default_name = Path.cwd().name  # default name is working dir name
        name = text('Model name?', default=default_name, validate=validate_non_empty).unsafe_ask()
        description = text('Model description?').unsafe_ask()

        model = create_model(api, name, description, model_type)


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


def blankly_deploy(args):
    with show_spinner('wheeeeeeeeeeeeeeeeee') as spinner:
        time.sleep(5)
        spinner.ok('YEET')
    raise NotImplementedError


def blankly_key(args):
    print(args)
    raise NotImplementedError


def blankly_add_key(args):
    print(args)
    raise NotImplementedError


def main():
    parser = argparse.ArgumentParser(description='Blankly CLI & deployment tool')
    subparsers = parser.add_subparsers(help='Core Blankly commands', required=True)

    init_parser = subparsers.add_parser('init', help='Initialize a new model in the current directory')
    init_parser.add_argument('-n', '--no-login', action='store_false', dest='prompt_login',
                             help='don\'t prompt to connect to Blankly Platform')
    init_parser.add_argument('--exchange', help='the exchange to connect to', choices=EXCHANGES)
    init_parser.add_argument('--name', help='the model name on the Blankly Platform')
    init_parser.add_argument('--description', help='the model description on the Blankly Platform')
    init_parser.add_argument('--template', help='the template to use for this model', choices=TEMPLATES)
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

    key_add_parser = key_subparsers.add_parser('add', help='Add an API Key to this model')
    key_add_parser.add_argument('--exchange', help='the exchange', choices=EXCHANGES)
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
