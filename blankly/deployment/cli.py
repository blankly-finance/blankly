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
import uuid
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
from blankly.utils.utils import load_json_file, info_print

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

        # TODO Add a very simple version that can take simple input() if this fails
        oldterm = termios.tcgetattr(fd)
        newattr = termios.tcgetattr(fd)
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

        index = int(input(TermColors.UNDERLINE + TermColors.OKCYAN + "You have chosen:" + TermColors.ENDC + " "))

        print('\n' + TermColors.BOLD + TermColors.WARNING + f"Chose {choice}:" + TermColors.ENDC + " " +
              TermColors.BOLD + TermColors.OKBLUE + options[index] + TermColors.ENDC)

        return options[index]


def get_project_model_and_name(args, projects):
    if args['path'] is None:
        print(TermColors.WARNING + "Warning - No filepath specified. Assuming the current directory (./)\n" +
              TermColors.ENDC)

        args['path'] = './'

    create_new = False
    general_description = None

    try:
        f = open(os.path.join(args['path'], deployment_script_name))
        deployment_options = json.load(f)

        f.close()
        if 'model_id' not in deployment_options or \
                'project_id' not in deployment_options or \
                'model_name' not in deployment_options:
            # This performs all the querying necessary to send the data up
            ids = []
            for i in projects:
                ids.append(i['projectId'])
            descriptions = []
            for i in projects:
                descriptions.append("\t" + TermColors.BOLD + TermColors.WARNING + i['projectId'] + ": " +
                                    TermColors.ENDC + TermColors.OKCYAN + i['name'])
            project_id = choose_option('project', ids, descriptions)

            model_name = input(TermColors.BOLD + TermColors.WARNING +
                               "Enter a name for your model: " + TermColors.ENDC)

            deployment_options['project_id'] = project_id
            deployment_options['model_id'] = str(uuid.uuid4())
            deployment_options['model_name'] = model_name

            create_new = True

            general_description = input(TermColors.BOLD + TermColors.WARNING +
                                        "Enter a general description for this model model: " + TermColors.ENDC)

            info_print(f"Generating new model id for this blankly.json: {deployment_options['model_id']}")
            # Write the modified version with the ID back into the json file
            f = open(os.path.join(args['path'], deployment_script_name), 'w+')
            f.write(json.dumps(deployment_options, indent=2))
            f.close()
        model_name = deployment_options['model_name']
        project_id = deployment_options['project_id']
        model_id = deployment_options['model_id']
    except FileNotFoundError:
        raise FileNotFoundError(f"A {deployment_script_name} file must be present at the top level of the "
                                f"directory specified.")

    python_version = deployment_options['python_version']
    return model_name, project_id, model_id, create_new, general_description, deployment_options, python_version


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

init_parser = subparsers.add_parser('init', help='Sub command to create a blankly-enabled development environment.')
init_parser.set_defaults(which='init')

login_parser = subparsers.add_parser('login', help='Log in to your blankly account.')
login_parser.set_defaults(which='login')

deploy_parser = subparsers.add_parser('deploy', help='Command to upload & start the model.')
deploy_parser.set_defaults(which='deploy')
add_path_arg(deploy_parser, required=False)

project_create_parser = subparsers.add_parser('create', help='Create a new project.')
project_create_parser.set_defaults(which='create')

backtest_parser = subparsers.add_parser('backtest', help='Start a backtest on an uploaded model.')
backtest_parser.set_defaults(which='backtest')
add_path_arg(backtest_parser, required=False)

list_parser = subparsers.add_parser('list', help='Show available projects & exit.')
list_parser.set_defaults(which='list')

run_parser = subparsers.add_parser('run', help='Mimic the run mechanism used in blankly deployment.')
run_parser.add_argument('--monitor',
                        action='store_true',
                        help='Add this flag to monitor the blankly process to understand CPU & memory usage. '
                             'The module psutil must be installed.')
run_parser.set_defaults(which='run')
add_path_arg(run_parser)

# Create a global token value for use in the double nested function below
token = None


def login(remove_cache: bool = False):
    # Set the token as global here
    global token
    from http.server import BaseHTTPRequestHandler, HTTPServer
    import urllib.parse

    fd, path = tempfile.mkstemp(prefix='blankly_auth_')
    temp_folder = os.path.dirname(path)
    file_name = os.path.basename(path)
    for i in os.listdir(temp_folder):
        # Check to see if one exists at this location
        if i[0:13] == 'blankly_auth_' and i != file_name:
            # If we're not removing cache this will use the old files to look for the token
            if not remove_cache:
                # If it's different from the one that was just created, remove the one just created
                os.close(fd)
                os.remove(os.path.join(temp_folder, file_name))
                # Reassign file name just in case its needed below to write into the file
                # Note that we protect against corrupted files below by overwriting any contents in case
                #  'token' not in token_file
                file_name = i
                # Now just read the token from it
                f = open(os.path.join(temp_folder, file_name))
                try:
                    token_file = json.load(f)

                    if 'token' in token_file:
                        # Exit cleanly here finding the old refresh token
                        return token_file['token']
                except json.decoder.JSONDecodeError:
                    # If it fails then don't return anything
                    #  just continue with re-logging in
                    pass
            # If we are removing cache then these files should just be deleted
            else:
                print(os.path.join(temp_folder, i))
                os.remove(os.path.join(temp_folder, i))
            # Be sure to leave the loop
            break

    def set_token(new_value):
        # Set the token as global here as well
        global token
        token = new_value

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
                set_token(args['token'][0])

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

        projects = api.list_projects()

        if len(projects) == 0:
            print(TermColors.FAIL + "Please create a project with 'blankly create' first." + TermColors.ENDC)
            return

        # Read and write to the deployment options if necessary
        model_name, project_id, model_id, create_new, general_description, deployment_options, python_version = \
            get_project_model_and_name(args, projects)

        info_print("Zipping...")

        model_path = zip_dir(args, deployment_options)

        chosen_plan = select_plan(api, 'live')

        version_description = input(TermColors.BOLD + TermColors.WARNING +
                                    "Enter a description for this version of the model: " + TermColors.ENDC)

        info_print("Uploading...")
        response = api.deploy(model_path,
                              project_id=project_id,
                              model_id=model_id,
                              plan=chosen_plan,
                              version_description=version_description,
                              general_description=general_description,
                              name=model_name,
                              create_new=create_new,
                              python_version=python_version)
        if 'error' in response:
            info_print('Error: ' + response['error'])
        elif 'status' in response and response['status'] == 'success':
            info_print(f"Model upload completed at {response['timestamp']}:")
            info_print(f"\tModel ID:\t{response['modelId']}")
            info_print(f"\tVersion:\t{response['versionId']}")
            info_print(f"\tStatus:  \t{response['status']}")
            info_print(f"\tProject:\t{response['projectId']}")

    elif which == 'init':
        print("Initializing...")
        print(very_important_string)

        # Directly download keys.json
        print("Downloading keys template...")
        keys_example = requests.get('https://raw.githubusercontent.com/Blankly-Finance/'
                                    'Blankly/main/examples/keys_example.json')
        create_and_write_file('keys.json', keys_example.text)

        # Directly download settings.json
        print("Downloading settings defaults...")
        settings = requests.get('https://raw.githubusercontent.com/Blankly-Finance/Blankly/main/examples/settings.json')
        create_and_write_file('settings.json', settings.text)

        # Directly download backtest.json
        print("Downloading backtest defaults...")
        backtest = requests.get('https://raw.githubusercontent.com/Blankly-Finance/Blankly/main/examples/backtest.json')
        create_and_write_file('backtest.json', backtest.text)

        # Directly download a rsi bot
        print("Downloading RSI bot example...")
        bot = requests.get('https://raw.githubusercontent.com/Blankly-Finance/Blankly/main/examples/rsi.py')
        create_and_write_file('bot.py', bot.text)

        print("Writing deployment defaults...")
        # Interpret defaults and write to this folder
        print("Detecting python version...")
        py_version = platform.python_version_tuple()
        print(f"{TermColors.OKCYAN}{TermColors.BOLD}Found python version: "
              f"{py_version[0]}.{py_version[1]}{TermColors.ENDC}")
        deploy = {
            "main_script": "./bot.py",
            "python_version": py_version[0] + "." + py_version[1],
            "requirements": "./requirements.txt",
            "working_directory": ".",
            "ignore_files": ['price_caches'],
            "backtest_args": {
                'to': '1y'
            }
        }
        create_and_write_file(deployment_script_name, json.dumps(deploy, indent=2))

        # Write in a blank requirements file
        print("Writing requirements.txt defaults...")
        create_and_write_file('requirements.txt', 'blankly')

        print(f"{TermColors.OKGREEN}{TermColors.UNDERLINE}Success!{TermColors.ENDC}")

    elif which == 'login':
        login(remove_cache=True)

    elif which == 'list':
        api = API(login())
        projects = api.list_projects()
        if len(projects) > 0:
            print(TermColors.BOLD + TermColors.WARNING + "Projects: " + TermColors.ENDC)
            for i in projects:
                print("\t" + TermColors.BOLD + TermColors.WARNING + i['projectId'] + ": " +
                      TermColors.ENDC + TermColors.OKCYAN + i['name'])
                print(f"\t\t Description: {i['description']}")
        else:
            info_print("No projects found.")

    elif which == 'backtest':
        api = API(login())

        projects = api.list_projects()

        # Read and write to the deployment options if necessary
        model_name, project_id, model_id, create_new, general_description, deployment_options, python_version = \
            get_project_model_and_name(args, projects)

        info_print("Zipping...")

        model_path = zip_dir(args, deployment_options)

        chosen_plan = select_plan(api, 'backtesting')

        backtest_description = input(TermColors.BOLD + TermColors.WARNING +
                                     "Enter a backtest description for this version of the model: " + TermColors.ENDC)

        response = api.backtest(project_id=project_id,
                                model_id=model_id,
                                args=deployment_options['backtest_args'],
                                backtest_description=backtest_description,
                                plan=chosen_plan,
                                file_path=model_path,
                                create_new=create_new,
                                python_version=python_version,
                                name=model_name)

        info_print("Uploading...")
        info_print(f"Backtest upload completed at {response['timestamp']}:")
        info_print(f"\tModel ID:\t{response['modelId']}")
        info_print(f"\tVersion:\t{response['versionId']}")
        info_print(f"\tStatus:  \t{response['status']}")
        info_print(f"\tProject:\t{response['projectId']}")

    elif which == 'create':
        api = API(login())

        project_name = input(TermColors.BOLD + "Input a name for your project: " + TermColors.ENDC)

        project_description = input(TermColors.BOLD + "Input a description for your project: " + TermColors.ENDC)

        input(TermColors.BOLD + TermColors.FAIL + "Press enter to confirm project creation." + TermColors.ENDC)

        response = api.create_project(project_name, description=project_description)

        if 'error' in response:
            info_print('Error: ' + response['error'])
        elif 'status' in response and response['status'] == 'success':
            info_print(f"Created {response['name']} at {response['createdAt']}:")
            info_print(f"\tProject Id:\t{response['projectId']}")
            info_print(f"\tStatus:\t{response['status']}")

    elif which == 'run':
        if args['path'] is None:
            run_parser.print_help()
        else:
            current_directory = os.getcwd()
            blankly_folder = os.path.join(current_directory, args['path'])
            deployment_location = os.path.join(blankly_folder, deployment_script_name)
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
