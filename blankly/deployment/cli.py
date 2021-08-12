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

parser = argparse.ArgumentParser(description='Blankly CLI & deployment tool.')


subparsers = parser.add_subparsers(help='Different blankly commands.')

init_parser = subparsers.add_parser('init', help='Sub command to create a blankly-enabled development environment.')
init_parser.set_defaults(which='init')

deploy_parser = subparsers.add_parser('deploy', help='Sub command to deploy the model.')
deploy_parser.set_defaults(which='deploy')

deploy_parser.add_argument('path',
                           metavar='path',
                           type=str,
                           nargs='?',
                           help='Path to the directory containing the blankly enabled deploy code.')


def main():
    args = vars(parser.parse_args())
    try:
        which = args['which']
    except KeyError:
        parser.print_help()
        return

    if which == 'deploy':
        pass
    elif which == 'init':
        pass


main()
