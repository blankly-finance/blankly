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
import warnings
import os
import platform


from blankly.utils.utils import load_json_file


def add_path_arg(arg_parser):
    arg_parser.add_argument('path',
                            metavar='path',
                            type=str,
                            help='Path to the directory containing the blankly enabled folder.')


parser = argparse.ArgumentParser(description='Blankly CLI & deployment tool.')


subparsers = parser.add_subparsers(help='Different blankly commands.')

init_parser = subparsers.add_parser('init', help='Sub command to create a blankly-enabled development environment.')
init_parser.set_defaults(which='init')

deploy_parser = subparsers.add_parser('deploy', help='Sub command to deploy the model.')
deploy_parser.set_defaults(which='deploy')

add_path_arg(deploy_parser)

run_parser = subparsers.add_parser('run', help='Mimic the run mechanism used in blankly deployment.')
run_parser.set_defaults(which='run')

add_path_arg(run_parser)


def main():
    args = vars(parser.parse_args())
    try:
        which = args['which']
    except KeyError:
        parser.print_help()
        return
    if which == 'deploy':
        if args['path'] is None:
            deploy_parser.print_help()
        else:
            pass
    elif which == 'init':
        pass
    elif which == 'run':
        if args['path'] is None:
            run_parser.print_help()
        else:
            current_directory = os.getcwd()
            blankly_folder = os.path.join(current_directory, args['path'])
            deployment_location = os.path.join(blankly_folder, 'deploy.json')
            try:
                # Find where the user specified their working directory and migrate to that
                deployment_dict = load_json_file(deployment_location)
            except FileNotFoundError:
                FileNotFoundError(f"Deployment json not found in location {deployment_location}.")
                return

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
                warnings.warn(warning_string)

            exec((open(os.path.join(blankly_folder, deployment_dict['main_script'])).read()))


main()
