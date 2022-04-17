"""
    Functions for blankly login/logout commands
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

import json
import pathlib
import sys
import urllib.parse
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Optional

from blankly.deployment.api import API
from blankly.deployment.ui import print_work, print_failure, print_success, show_spinner

SUCCESS_URL = 'https://firebasestorage.googleapis.com/v0/b/blankly-6ada5.appspot.com/o/login_success.html?alt=media&token=41d734e2-0a88-44c4-b1dd-7e081fd019e7'
FAILURE_URL = 'https://firebasestorage.googleapis.com/v0/b/blankly-6ada5.appspot.com/o/login_failure.html?alt=media&token=b2d9f6dc-aa54-4da2-aa6f-1f75a4025634'



def write_token(token):
    token_file = get_token_file()
    token_file.parent.mkdir(parents=True, exist_ok=True)
    with open(token_file, 'w') as file:
        json.dump({'token': token}, file)


def poll_login() -> Optional[API]:
    # mutate a list to avoid needing global variable shit and piss
    token = []

    class TokenListener(BaseHTTPRequestHandler):
        def do_GET(self):
            try:
                token.append(urllib.parse.parse_qs(self.path[2:])['token'][0])
                self.send_response_only(302)
                self.send_header('Location', SUCCESS_URL)
                self.end_headers()
            except Exception:
                token.append(False)
                self.send_response(302)
                self.send_header('Location', FAILURE_URL)  # send them back lmao
                self.end_headers()

    server = HTTPServer(('', 9082), TokenListener)

    while not token:
        server.handle_request()
    token = token[0]

    if token:
        api = API(token)
        write_token(token)
        return api




def get_token() -> Optional[str]:
    token_file = get_token_file()
    if token_file.exists():
        # file exists, parse it or error out
        with open(token_file, 'r') as file:
            data = json.load(file)
        return data['token']
    return None


def get_token_file() -> pathlib.Path:
    return get_datadir() / 'blankly' / 'auth.json'


# https://stackoverflow.com/a/61901696
def get_datadir() -> pathlib.Path:
    """
    Returns a parent directory path where persistent application data can be stored.

    # linux: ~/.local/share
    # macOS: ~/Library/Application Support
    # windows: C:/Users/<USER>/AppData/Roaming
    """

    home = pathlib.Path.home()

    if sys.platform == "win32":
        return home / "AppData/Roaming"
    elif sys.platform == "darwin":
        return home / "Library/Application Support"
    elif sys.platform.startswith("linux"):
        return home / ".local/share"
    return home


def logout():
    # python 3.8 has a parameter for this `missing_ok` but we need to support 3.7
    try:
        get_token_file().unlink()
    except FileNotFoundError:
        pass
