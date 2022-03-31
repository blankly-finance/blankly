"""
    CLI for interacting with and uploading blankly models.
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

import argparse
import sys
import traceback
import warnings
import os
import platform
import runpy
import time
import requests
import json
import zipfile
import tempfile
import webbrowser

from blankly.deployment.api import API
from blankly.utils.utils import load_json_file, info_print, load_deployment_settings

very_important_string = """
██████╗ ██╗      █████╗ ███╗   ██╗██╗  ██╗██╗  ██╗   ██╗    ███████╗██╗███╗   ██╗ █████╗ ███╗   ██╗ ██████╗███████╗
██╔══██╗██║     ██╔══██╗████╗  ██║██║ ██╔╝██║  ╚██╗ ██╔╝    ██╔════╝██║████╗  ██║██╔══██╗████╗  ██║██╔════╝██╔════╝
██████╔╝██║     ███████║██╔██╗ ██║█████╔╝ ██║   ╚████╔╝     █████╗  ██║██╔██╗ ██║███████║██╔██╗ ██║██║     █████╗  
██╔══██╗██║     ██╔══██║██║╚██╗██║██╔═██╗ ██║    ╚██╔╝      ██╔══╝  ██║██║╚██╗██║██╔══██║██║╚██╗██║██║     ██╔══╝  
██████╔╝███████╗██║  ██║██║ ╚████║██║  ██╗███████╗██║       ██║     ██║██║ ╚████║██║  ██║██║ ╚████║╚██████╗███████╗
╚═════╝ ╚══════╝╚═╝  ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝╚═╝       ╚═╝     ╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚═╝  ╚═══╝ ╚═════╝╚══════╝
"""

deployment_script_name = 'blankly.json'


# From blender build scripts found at
# https://stackoverflow.com/a/287944/8087739
class TermColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


supported_exchanges = ['binance.com', 'binance.us',
                       'coinbase_pro', 'alpaca', 'ftx', 'oanda', 'getting-started']


def choose_option(choice: str, options: list, descriptions: list):
    """
    Generalized CLI tool to choose between given options

    Args:
        choice: String for "Choose a <choice>" shown to the user
        options: List of string options allowed ex: ['micro', 'small', 'medium']
        descriptions: Description to show for each option corresponding to the earlier options: ex: ['
            miocro:
                CPU: 5,
                RAM: 10
        ']
    """

    def print_descriptions(descriptions_: list, show_index: bool):
        index_ = 0
        for j in descriptions_:
            if show_index:
                j = TermColors.ENDC + str(index_) + ": " + j
            print(j)
            index_ += 1

    try:
        import fcntl
        import termios
        fd = sys.stdin.fileno()

        largest_option_name = 0
        for i in options:
            if len(i) > largest_option_name:
                largest_option_name = len(i)

        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)

        def print_selection_index(index_):
            # We pass none when they haven't selected yet
            if index_ is None:
                chosen_plan = "None"
            # When its given a number it will index and find the lengths
            else:
                if index_ < 0:
                    index_ = len(options) - 1
                elif index_ >= len(options):
                    index_ = 0
                chosen_plan = options[index_]

            # Carry it in this string
            string_ = "\r" + TermColors.UNDERLINE + TermColors.OKCYAN + "You have chosen: " + \
                      TermColors.ENDC + " " + TermColors.BOLD + TermColors.OKBLUE + chosen_plan

            remaining_chars = largest_option_name - len(chosen_plan)
            string_ += " " * remaining_chars

            # Final print and flush the buffer
            sys.stdout.write(string_)
            sys.stdout.flush()

            return index_

        print(TermColors.BOLD + TermColors.WARNING + f"Choose a {choice}: " + TermColors.ENDC +
              TermColors.UNDERLINE + "(Use your arrow keys ← →)" + TermColors.ENDC)

        # Print everything out with no index
        print_descriptions(descriptions, False)

        newattr[3] = newattr[3] & ~termios.ICANON & ~termios.ECHO
        termios.tcsetattr(fd, termios.TCSANOW, newattr)

        oldflags = fcntl.fcntl(fd, fcntl.F_GETFL)
        fcntl.fcntl(fd, fcntl.F_SETFL, oldflags | os.O_NONBLOCK)

        index = 0
        print_selection_index(None)
        try:
            while True:
                try:
                    c = sys.stdin.read(1)
                    if c == '[':
                        c = sys.stdin.read(1)
                        if c == 'C':
                            index += 1
                            index = print_selection_index(index)
                        elif c == 'D':
                            index -= 1
                            index = print_selection_index(index)
                    elif c == '\n':
                        break
                except IOError:
                    pass
        finally:
            termios.tcsetattr(fd, termios.TCSAFLUSH, oldterm)
            fcntl.fcntl(fd, fcntl.F_SETFL, oldflags)

        print('\n' + TermColors.BOLD + TermColors.WARNING + f"Chose {choice}:" + TermColors.ENDC + " " +
              TermColors.BOLD + TermColors.OKBLUE + options[index] + TermColors.ENDC)

        return options[index]
    except Exception:
        # info_print("Using non-interactive selection on this device.")

        print_descriptions(descriptions, True)

        print(TermColors.BOLD + TermColors.WARNING + f"Choose a {choice}: " + TermColors.ENDC +
              TermColors.UNDERLINE + "(Input the index of your selection)" + TermColors.ENDC)

        index = int(input(TermColors.UNDERLINE + TermColors.OKCYAN +
                    "You have chosen:" + TermColors.ENDC + " "))

        if index < 0 or index > len(options) - 1:
            raise LookupError(f"The index you chose is out of bounds, choose an index between {0} and "
                              f"{len(options) -1}")

        print('\n' + TermColors.BOLD + TermColors.WARNING + f"Chose {choice}:" + TermColors.ENDC + " " +
              TermColors.BOLD + TermColors.OKBLUE + options[index] + TermColors.ENDC)

        return options[index]


def get_project_model_and_name(args, api: API):
    if 'path' not in args or args['path'] is None:
        print(TermColors.WARNING + "Warning - No filepath specified. Assuming the current directory (./)\n" +
              TermColors.ENDC)

        args['path'] = './'

    try:
        f = open(os.path.join(args['path'], deployment_script_name))
        deployment_options = json.load(f)
        f.close()

        # Use this variable to always write if something has changed
        queue_write = False
        """
        This handles identifying the project on login
        """
        if 'model_id' not in deployment_options or \
                'type' not in deployment_options or \
                'model_name' not in deployment_options:
            # This performs all the querying necessary to send the data up
            choice = choose_option('way to connect to a model', ['Create New', 'Choose from Existing'],
                                   ['Generate a new model',
                                    'Attach to an existing model'])

            if choice == 'Create New':
                model_name = input(TermColors.BOLD + TermColors.WARNING +
                                   "Enter a name for your model: " + TermColors.ENDC)

                # Now we know to go ahead and create a new model on the server
                general_description = input(TermColors.BOLD + TermColors.WARNING +
                                            "Enter a general description for this model model: " + TermColors.ENDC)

                type_ = choose_option('model type', ['strategy', 'screener'],
                                      ["\t" + TermColors.BOLD + TermColors.WARNING +
                                       'A strategy is a model that uses blankly.Strategy' + TermColors.ENDC,
                                       "\t" + TermColors.BOLD + TermColors.WARNING +
                                       'A screener is a model uses blankly.Screener' + TermColors.ENDC])

                model_id = api.create_model(type_, model_name, general_description)['modelId']
            else:
                models = api.list_models()
                ids = []
                descriptions = []
                for i in models:
                    try:
                        id_ = i['id']
                        name_ = i['name']
                        ids.append(id_)
                        descriptions.append("\t" + TermColors.BOLD + TermColors.WARNING + id_ + ": " +
                                            TermColors.ENDC + TermColors.OKCYAN + name_)
                    except KeyError:
                        pass
                model_id = choose_option('model', ids, descriptions)

                # Because we have the ID, we now need to get the index directly
                index = None
                for i in models:
                    if i['id'] == model_id:
                        index = i

                if index is None:
                    raise LookupError("An issue occurred please try again.")

                type_ = index['type']
                model_name = index['name']

            info_print(f"Created a new model in blankly.json with ID: {model_id}")

            deployment_options['type'] = type_
            deployment_options['model_id'] = model_id
            deployment_options['model_name'] = model_name
        model_name = deployment_options['model_name']

        """
        This part generates API keys if they aren't found
        """
        if 'api_key' not in deployment_options or 'api_pass' not in deployment_options:
            response = api.generate_keys()
            deployment_options['api_key'] = response['apiKey']
            deployment_options['api_pass'] = response['apiPass']
            queue_write = True

        if queue_write:
            # Write the modified version with the ID back into the json file
            f = open(os.path.join(args['path'], deployment_script_name), 'w+')
            f.write(json.dumps(deployment_options, indent=2))
            f.close()
    except FileNotFoundError:
        raise FileNotFoundError(f"A {deployment_script_name} file must be present at the top level of the "
                                f"directory specified.")

    python_version = deployment_options['python_version']
    return model_name, deployment_options, python_version


temporary_zip_file = None


def zip_dir(args: dict, deployment_options: dict):
    global temporary_zip_file
    temporary_zip_file = tempfile.TemporaryDirectory()
    dist_directory = temporary_zip_file.__enter__()

    # dist_directory = tempfile.TemporaryDirectory().__enter__()
    # with tempfile.TemporaryDirectory() as dist_directory:
    source = os.path.abspath(args['path'])

    model_path = os.path.join(dist_directory, 'model.zip')
    zip_ = zipfile.ZipFile(model_path, 'w', zipfile.ZIP_DEFLATED)
    zipdir(source, zip_, deployment_options['ignore_files'])
    zip_.close()

    return model_path


def select_plan(api: API, plan_type: str):
    plans = api.get_plans(plan_type)

    plan_names = list(plans.keys())

    descriptions = []

    for i in plans:
        descriptions.append("\t" + TermColors.UNDERLINE + TermColors.OKBLUE + i + TermColors.ENDC +
                            "\n\t\t" + TermColors.OKGREEN + 'CPU: ' + str(plans[i]['cpu']) +
                            "\n\t\t" + TermColors.OKGREEN + 'RAM: ' + str(plans[i]['ram']) + TermColors.ENDC)

    chosen_plan = choose_option('plan', plan_names, descriptions)

    return chosen_plan


def add_path_arg(arg_parser, required=True):
    kwargs = {
        'metavar': 'path',
        'type': str,
        'help': 'Path to the directory containing the blankly enabled folder.',
        'nargs': '?'
    }
    # Pass this along if its not required
    if not required:
        kwargs['nargs'] = '?'
    arg_parser.add_argument('path', **kwargs)


def create_and_write_file(filename: str, default_contents: str = None):
    try:
        file = open("./" + filename, 'x+')
        if default_contents is not None:
            file.write(default_contents)
    except FileExistsError:
        print(f"{TermColors.WARNING}Already exists - skipping...{TermColors.ENDC}")


parser = argparse.ArgumentParser(description='Blankly CLI & deployment tool.')

subparsers = parser.add_subparsers(help='Different blankly commands.')

supported_exchanges_str = ''
for i in supported_exchanges:
    supported_exchanges_str += i + "\n"

init_parser = subparsers.add_parser('init', help=f'Sub command to create a blankly-enabled development environment.'
                                                 f' Supports blankly init on these exchanges: '
                                                 f'\n{supported_exchanges_str}- Ex: \'blankly init coinbase_pro\'')
init_parser.set_defaults(which='init')
# Generate a help message specific to this command
init_help_message = 'One of the following supported exchanges: \n'
for i in supported_exchanges:
    init_help_message += i + "\n"
init_parser.add_argument('exchange', nargs='?', default='none', type=str, help=init_help_message)

login_parser = subparsers.add_parser('login', help='Log in to your blankly account.')
login_parser.set_defaults(which='login')

login_parser = subparsers.add_parser('logout', help='Log out of your blankly account.')
login_parser.set_defaults(which='logout')

deploy_parser = subparsers.add_parser('deploy', help='Command to upload & start the model.')
deploy_parser.set_defaults(which='deploy')
add_path_arg(deploy_parser, required=False)

# Old project tools
# project_create_parser = subparsers.add_parser('create', help='Create a new project.')
# project_create_parser.set_defaults(which='create')
# list_parser = subparsers.add_parser('list', help='Show available projects & exit.')
# list_parser.set_defaults(which='list')

backtest_parser = subparsers.add_parser('backtest', help='Start a backtest on an uploaded model.')
backtest_parser.set_defaults(which='backtest')
add_path_arg(backtest_parser, required=False)


run_parser = subparsers.add_parser('run', help='Mimic the run mechanism used in blankly deployment.')
run_parser.add_argument('--monitor',
                        action='store_true',
                        help='Add this flag to monitor the blankly process to understand CPU & memory usage. '
                             'The module psutil must be installed.')
run_parser.set_defaults(which='run')
add_path_arg(run_parser)

# Create a global token value for use in the double nested function below
token = None
tokenfile_path = None


def __generate_tempfile():
    """
    Generate a temporary file with the blankly auth prefix and then get the directory / file name from it
    """
    fd, path = tempfile.mkstemp(prefix='blankly_auth_')
    temp_folder = os.path.dirname(path)
    file_name = os.path.basename(path)

    return fd, temp_folder, file_name


def logout():
    """
    This function will log out if not logged in
    """
    global tokenfile_path
    fd, temp_folder, file_name = __generate_tempfile()
    os.close(fd)
    os.remove(os.path.join(temp_folder, file_name))
    for i_ in os.listdir(temp_folder):
        # Check to see if one exists at this location
        if i_[0:13] == 'blankly_auth_' and i_ != file_name:
            # Kill the file we created
            os.remove(os.path.join(temp_folder, i_))


def is_logged_in():
    """
    This function will return if the user is logged in

    logged_in = __is_logged_in(temp_folder) is not None
    """
    global tokenfile_path
    fd, temp_folder, file_name = __generate_tempfile()
    for i_ in os.listdir(temp_folder):
        # Check to see if one exists at this location
        if i_[0:13] == 'blankly_auth_' and i_ != file_name:
            # Kill the file we created
            os.close(fd)
            os.remove(os.path.join(temp_folder, file_name))
            
            try:
                json.loads(open(temp_folder + '/' + i_).read())['token']
            except (KeyError, json.decoder.JSONDecodeError):
                return False

            # Cache the filepath globally
            tokenfile_path = os.path.join(temp_folder, i_)
            return True

    # Kill the file we created
    os.close(fd)
    os.remove(os.path.join(temp_folder, file_name))
    return False


def login(remove_cache: bool = False):
    # Set the token as global here
    global token
    # Also get the global path
    global tokenfile_path

    def load_token(token_path_: str) -> str:
        """
        If the file has the token then this function is a success
        """
        global tokenfile_path
        global token
        f_ = open(token_path_)
        token_file_ = json.load(f_)

        if 'token' in token_file_:
            # Globally cache the path
            tokenfile_path = token_path_
            # Globally cache the token
            token = token_file_['token']

            # Exit cleanly here finding the old refresh token
            return token_file_['token']

    # This can be skipped if is_logged_in is run which will find the temp folder and file name if necessary
    if tokenfile_path is None:
        fd, temp_folder, file_name = __generate_tempfile()
        for i_ in os.listdir(temp_folder):
            # Check to see if one exists at this location
            if i_[0:13] == 'blankly_auth_' and i_ != file_name:
                # If we're not removing cache this will use the old files to look for the token
                if not remove_cache:
                    # If it's different from the one that was just created, remove the one just created
                    os.close(fd)
                    os.remove(os.path.join(temp_folder, file_name))
                    # Reassign file name just in case its needed below to write into the file
                    # Note that we protect against corrupted files below by overwriting any contents in case
                    #  'token' not in token_file
                    file_name = i_
                    # Now just read the token from it
                    token_path = os.path.join(temp_folder, file_name)
                    try:
                        return load_token(token_path)
                    except json.decoder.JSONDecodeError:
                        # If it fails then don't return anything
                        #  just continue with re-logging in
                        pass
                # If we are removing cache then these files should just be deleted
                else:
                    os.remove(os.path.join(temp_folder, i_))
                # Be sure to leave the loop
                break
    elif isinstance(tokenfile_path, str):
        return load_token(tokenfile_path)

    from http.server import BaseHTTPRequestHandler, HTTPServer
    import urllib.parse

    class Handler(BaseHTTPRequestHandler):
        token: str

        def do_OPTIONS(self):
            # This options call is not used however these headers were hard to figure out, so I'm leaving them
            self.send_response(200, "ok")
            self.send_header('Access-Control-Allow-Origin', 'https://app.blankly.finance')
            self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
            self.send_header("Access-Control-Allow-Headers", 'Accept,Origin,Content-Type,X-LS-CORS-Template,'
                                                             'X-LS-Auth-Token,X-LS-Auth-User-Token,Content-Type,'
                                                             'X-LS-Sync-Result,X-LS-Sequence,token')
            self.end_headers()

        def do_GET(self):
            global token
            # Parse the URL
            args = urllib.parse.parse_qs(self.path[2:])
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()

            # Send this to the global static variable to use the info out of this
            if 'token' in args and args['token'] is not None:
                # Perform a GET request to pull down a successful response
                file = requests.get('https://firebasestorage.googleapis.com/v0/b/blankly-6ada5.appspot.com/o/'
                                    'login_success.html?alt=media&token=41d734e2-0a88-44c4-b1dd-7e081fd019e7')
                token = args['token'][0]

                info_print("Login success - You can close your browser.")
            else:
                file = requests.get('https://firebasestorage.googleapis.com/v0/b/blankly-6ada5.appspot.com/o/'
                                    'login_failure.html?alt=media&token=b2d9f6dc-aa54-4da2-aa6f-1f75a4025634')
                info_print("Failed to login - please try again.")

            # Write that back to the user
            self.wfile.write(bytes(file.text, "utf8"))

        def log_message(self, format_, *args):
            return

    server = HTTPServer(('', 9082), Handler)

    # Attempt to open the page
    url = 'https://app.blankly.finance/auth/signin?redirectUrl=/deploy'
    webbrowser.open_new(url)

    info_print('Log in on the pop-up window or navigate to: \nhttps://app.blankly.finance/auth/'
               'signin?redirectUrl=/deploy')

    # Continue waiting for GETs while the token is undefined
    while token is None:
        server.handle_request()

    cached_token_file = open(os.path.join(temp_folder, file_name), "w")
    json.dump({'token': token}, cached_token_file)

    return token


def zipdir(path, ziph, ignore_files: list):
    # From https://stackoverflow.com/a/1855118/8087739
    # Notice we're using this instead of shutil because it allows customization such as passwords and skipping
    # directories
    # ziph is zipfile handle

    filtered_ignore_files = []
    # Set all the ignored files to be absolute
    for i in range(len(ignore_files)):
        # Reject this case
        if ignore_files[i] == "":
            continue
        filtered_ignore_files.append(os.path.abspath(ignore_files[i]))

    for root, dirs, files in os.walk(path, topdown=True):
        for file in files:
            # (Modification) Skip everything that is in the blankly_dist folder
            filepath = os.path.join(root, file)

            if not (os.path.abspath(filepath) in filtered_ignore_files) and not (root in filtered_ignore_files):
                # This takes of the first part of the relative path and replaces it with /model/
                print(f'\tAdding: {file} in folder {root}.')
                relpath = os.path.relpath(filepath,
                                          os.path.join(path, '..'))
                relpath = os.path.normpath(relpath).split(os.sep)
                relpath[0] = os.sep + 'model'
                relpath = os.path.join(*relpath)

                ziph.write(filepath, relpath)
            else:
                info_print(f'\tSkipping: {file} in folder {root}.')


def main():
    args = vars(parser.parse_args())
    try:
        which = args['which']
    except KeyError:
        parser.print_help()
        return
    if which == 'deploy':
        token_ = login()

        api = API(token_)

        # Read and write to the deployment options if necessary
        model_name, deployment_options, python_version = \
            get_project_model_and_name(args, api)

        info_print("Zipping...")

        model_path = zip_dir(args, deployment_options)

        chosen_plan = select_plan(api, 'live')

        version_description = input(TermColors.BOLD + TermColors.WARNING +
                                    "Enter a description for this version of the model: " + TermColors.ENDC)

        info_print("Uploading...")
        kwargs = {
            'file_path': model_path,
            'model_id': deployment_options['model_id'],
            'version_description': version_description,
            'python_version': python_version,
            'type_': deployment_options['type'],
            'plan': chosen_plan
        }
        if kwargs['type_'] == 'screener':
            kwargs['schedule'] = deployment_options['screener']['schedule']

        response = api.deploy(**kwargs)
        if 'error' in response:
            info_print('Error: ' + response['error'])
        elif 'status' in response and response['status'] == 'success':
            info_print(f"Model upload completed at {response['timestamp']}:")
            info_print(f"\tModel ID:\t{response['modelId']}")
            info_print(f"\tVersion:\t{response['versionId']}")
            info_print(f"\tStatus:  \t{response['status']}")
            url = f"https://app.blankly.finance/{api.user_id}/{response['modelId']}/overview"
            webbrowser.open(url)
            info_print(f"\tView your model here: {url}")

    elif which == 'init':
        exchange = args['exchange']
        if exchange != 'none':
            user_defined_exchange = exchange.lower()
        else:
            user_defined_exchange = 'coinbase_pro'  # default to cbpro

        print("Initializing...")
        try:
            print(very_important_string)
        except UnicodeEncodeError:
            print("Welcome to blankly!")

        if user_defined_exchange not in supported_exchanges:
            base_str = 'Error: Please use one of our supported exchanges'
            exchanges = ', '.join(supported_exchanges)
            info_print(
                f'{base_str}: {TermColors.BOLD}{exchanges}{TermColors.ENDC}. '
                f'\nYour input: {TermColors.BOLD}{user_defined_exchange}{TermColors.ENDC}')
            return

        tld = 'com'
        if user_defined_exchange[0:7] == 'binance':
            # Find if it's .us if needed
            tld = user_defined_exchange[8:]
            user_defined_exchange = 'binance'

        exchange_config = {
            'settings.json': 'https://raw.githubusercontent.com/blankly-finance/examples/main/configs/settings.json',
            'keys.json': 'https://raw.githubusercontent.com/blankly-finance/examples/main/keys_example.json',
            'backtest_usd.json': 'https://raw.githubusercontent.com/blankly-finance/examples/main/configs/'
                                 'backtest_usd.json',
            'exchange': user_defined_exchange,
            'bot_url': f'https://raw.githubusercontent.com/blankly-finance/examples/main/init/rsi_'
                       f'{user_defined_exchange}.py',
            'tld': tld,
        }

        # Directly download keys.json
        print("Downloading keys template...")
        keys_example = requests.get(exchange_config['keys.json']).json()
        # No modification necessary
        create_and_write_file('keys.json', json.dumps(keys_example, indent=2))

        # Directly download settings.json
        print("Downloading settings defaults...")
        settings = requests.get(exchange_config['settings.json']).json()
        # Make sure we write the tld into the settings
        settings['settings']['binance']['binance_tld'] = exchange_config['tld']
        create_and_write_file('settings.json', json.dumps(settings, indent=2))

        # Directly download backtest.json
        print("Downloading backtest defaults...")
        backtest = requests.get(exchange_config['backtest_usd.json']).json()
        if user_defined_exchange == 'kucoin' or user_defined_exchange == 'binance':
            # USDT exchanges
            backtest['settings']['quote_account_value_in'] = 'USDT'
        create_and_write_file('backtest.json', json.dumps(backtest, indent=2))

        # Directly download a rsi bot
        print("Downloading RSI bot example...")
        bot = requests.get(exchange_config['bot_url'])
        create_and_write_file('bot.py', bot.text)

        print("Writing deployment defaults...")
        # Interpret defaults and write to this folder
        print("Detecting python version...")
        py_version = platform.python_version_tuple()
        print(f"{TermColors.OKCYAN}{TermColors.BOLD}Found python version: "
              f"{py_version[0]}.{py_version[1]}{TermColors.ENDC}")

        # Write in a blank requirements file
        print("Writing requirements.txt defaults...")
        create_and_write_file('requirements.txt', 'blankly')

        deploy = load_deployment_settings()

        deploy['python_version'] = py_version[0] + "." + py_version[1]
        create_and_write_file(deployment_script_name, json.dumps(deploy, indent=2))

        try:
            if is_logged_in():
                # We know we're logged in so make sure that we also get a project id and a model id
                print(f'{TermColors.WARNING}Automatically logged in!{TermColors.ENDC}')
                api = API(login())
                print(f'{TermColors.WARNING}Attaching this to a platform model...{TermColors.ENDC}')
                get_project_model_and_name(args, api)
            else:
                print(f'{TermColors.WARNING}Run \"blankly login\" and then \"blankly init\" again to get better '
                      f'backtest '
                      f'viewing.{TermColors.ENDC}')
        except Exception:
            traceback.print_exc()
            # Wipe the blankly.json to avoid confusion
            os.remove('./' + deployment_script_name)

        print(f"{TermColors.OKGREEN}{TermColors.UNDERLINE}Success!{TermColors.ENDC}")

    elif which == 'login':
        login(remove_cache=True)

    elif which == 'logout':
        logout()
        info_print("Cleared all blankly credentials.")

    # elif which == 'list':
    #     api = API(login())
    #     models = api.list_models()
    #     if len(models) > 0:
    #         print(TermColors.BOLD + TermColors.WARNING + "Models: " + TermColors.ENDC)
    #         for i in models:
    #             print("\t" + TermColors.BOLD + TermColors.WARNING + i['id'] + ": " +
    #                   TermColors.ENDC + TermColors.OKCYAN + i['name'])
    #             print(f"\t\t Description: {i['description']}")
    #     else:
    #         info_print("No projects found.")

    elif which == 'backtest':
        api = API(login())

        # Read and write to the deployment options if necessary
        model_name, deployment_options, python_version = get_project_model_and_name(args, api)

        if deployment_options['type'] == 'screener':
            raise AttributeError("Screeners are not backtestable.")

        info_print("Zipping...")

        model_path = zip_dir(args, deployment_options)

        chosen_plan = select_plan(api, 'backtesting')

        backtest_description = input(TermColors.BOLD + TermColors.WARNING +
                                     "Enter a backtest description for this version of the model: " + TermColors.ENDC)
        info_print("Uploading...")

        response = api.backtest(file_path=model_path,
                                model_id=deployment_options['model_id'],
                                args=deployment_options['backtest_args'],
                                plan=chosen_plan,
                                python_version=python_version,
                                backtest_description=backtest_description,
                                type_=deployment_options['type'])

        info_print("Uploading...")
        if 'error' in response:
            info_print(response['error'])
        else:
            info_print(f"Backtest upload completed at {response['timestamp']}:")
            info_print(f"\tModel ID:\t{response['modelId']}")
            info_print(f"\tVersion:\t{response['versionId']}")
            info_print(f"\tStatus:  \t{response['status']}")

    # elif which == 'create':
    #     api = API(login())
    #
    #     project_name = input(TermColors.BOLD + "Input a name for your model: " + TermColors.ENDC)
    #
    #     project_description = input(TermColors.BOLD + "Input a description for your model: " + TermColors.ENDC)
    #
    #     input(TermColors.BOLD + TermColors.FAIL + "Press enter to confirm model creation." + TermColors.ENDC)
    #
    #     response = api.create_model(type_='strategy', name=project_name, description=project_description)
    #
    #     if 'error' in response:
    #         info_print('Error: ' + response['error'])
    #     elif 'status' in response and response['status'] == 'success':
    #         info_print(f"Created {response['name']} at {response['createdAt']}:")
    #         info_print(f"\tModel Id:\t{response['id']}")

    elif which == 'run':
        if args['path'] is None:
            run_parser.print_help()
        else:
            current_directory = os.getcwd()
            blankly_folder = os.path.join(current_directory, args['path'])
            deployment_location = os.path.join(
                blankly_folder, deployment_script_name)
            try:
                # Find where the user specified their working directory and migrate to that
                deployment_dict = load_json_file(deployment_location)
            except FileNotFoundError:
                raise FileNotFoundError(f"Deployment json not found in location {deployment_location}.")

            # Set the working directory to match the deployment dictionary
            os.chdir(os.path.join(blankly_folder, deployment_dict['working_directory']))

            current_version = platform.python_version_tuple()
            current_version = current_version[0] + "." + current_version[1]

            if current_version != str(deployment_dict['python_version']):
                warn_string = f"Specified python version different than current interpreter. Using version " \
                              f"{platform.python_version()}. The specified version will be followed on full" \
                              f" deployment."
                warnings.warn(warn_string)

            if 'requirements' in deployment_dict and deployment_dict['requirements'] is not None:
                warning_string = "Requirements specified but not installed in this test script. Install " \
                                 "manually if needed."
                info_print(warning_string)

            sys.path.append(blankly_folder)

            # The execute function to run the modules
            main_script_abs = os.path.abspath(deployment_dict['main_script'])
            runpy.run_path(main_script_abs, {}, "__main__")

            if args['monitor']:
                try:
                    import psutil
                except ImportError:
                    raise ImportError("Must install psutil (pip install psutil) to monitor "
                                      "the Blankly process")
                print("Process must be killed to halt monitoring.")

                pid = os.getpid()
                process = psutil.Process(pid)
                while True:
                    monitor_string = "\rCPU Usage: "
                    monitor_string += str(process.cpu_percent())
                    monitor_string += " | "
                    monitor_string += "Memory Usage: "
                    monitor_string += str(process.memory_percent())
                    sys.stdout.write(monitor_string)
                    sys.stdout.flush()
                    time.sleep(5)


if __name__ == "__main__":
    main()
