"""
    ZeroMQ server for communicating with other languages or GUIs
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

import time
import zmq
from zmq.error import Again
import threading

#
# from __future__ import print_function
#
# import sys
#
# import zerorpc
#
# import blankly
# from blankly.utils.calc import calc as real_calc
#
#
# # Tickers shouldn't be accessed from this class. Interfaces will not have access to them
# class TradeInterface:
#     def __init__(self):
#         self.__auth_path = None
#         self.__preferences_path = None
#         self.__exchanges = []
#
#     def calc(self, text):
#         """ Very basic connectivity test, given a string compute the output """
#         return real_calc(text)
#
#     def echo(self, text):
#         """echo any text """
#         return text
#
#     def init(self, auth_path, preferences_path):
#         # Called from the dashboard
#         self.__exchanges = []
#         self.__auth_path = auth_path
#         self.__preferences_path = preferences_path
#
#     def create_portfolio(self, exchange_type, portfolio_name):
#         if exchange_type == "coinbase_pro":
#             self.__exchanges.append(blankly.CoinbasePro(portfolio_name=portfolio_name,
#                                                         keys_path=self.__auth_path,
#                                                         settings_path=self.__preferences_path))
#         elif exchange_type == "binance":
#             self.__exchanges.append(blankly.Binance(portfolio_name=portfolio_name,
#                                                     keys_path=self.__auth_path,
#                                                     settings_path=self.__preferences_path))
#         else:
#             raise ValueError("Exchange not found or unsupported")
#
#     """ External State """
#
#     def get_exchange_state(self, name):
#         for i in range(len(self.__exchanges)):
#             if self.__exchanges[i].get_name() == name:
#                 return [self.__exchanges[i].get_exchange_state(), name]
#
#     """
#     Internal State, this has all the currencies. This is mainly used for an initial definition of which currencies
#     are being used, get model state is what will matter for the reporting into these blocks
#     """
#
#     def get_portfolio_state(self, name):
#         for i in range(len(self.__exchanges)):
#             if self.__exchanges[i].get_name() == name:
#                 return [self.__exchanges[i].__get_portfolio_state(), name]
#
#     def run_model(self, name, currency_pair=None):
#         for i in range(len(self.__exchanges)):
#             if self.__exchanges[i].get_name() == name:
#                 self.__exchanges[i].start_models(currency_pair)
#
#     def assign_model(self, portfolio_name, currency_pair, model_name, args=None):
#         for i in range(len(self.__exchanges)):
#             if self.__exchanges[i].get_name() == portfolio_name:
#                 self.__exchanges[i].append_model(model_name, currency_pair, args)
#
#     """
#     Three indicators at the top of the GUI - JSON with only 3 keys
#     """
#
#     def update_indicators(self, name):
#         for i in range(len(self.__exchanges)):
#             if self.__exchanges[i].get_name() == name:
#                 return self.__exchanges[i].get_indicators()
#
#
# def parse_port():
#     port = 4242
#     try:
#         port = int(sys.argv[1])
#     except Exception as e:
#         pass
#     return '{}'.format(port)
#
#
# def main():
#     addr = 'tcp://127.0.0.1:' + parse_port()
#     s = zerorpc.Server(TradeInterface())
#     s.bind(addr)
#     print('start running on {}'.format(addr))
#     s.run()
#
#
# if __name__ == '__main__':
#     main()


class Connection:
    def __init__(self):

        # Create a thread an a global connection variable
        self.__thread = None
        self.connected = False

        # Setup zmq connection prereqs
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REP)

        self.reattempt_connection()

    def reattempt_connection(self):
        if not self.connected:
            self.__thread = threading.Thread(target=self.__establish_connection, daemon=True)
            self.__thread.start()

    def __establish_connection(self):
        try:
            self.socket.bind("tcp://*:5555")
        except zmq.error.ZMQError:
            # If logging is implemented this could write to the log in the background
            pass

        # Set a timeout of ten seconds to connect
        self.socket.set(zmq.RCVTIMEO, 10000)

        try:
            # Wait the delay time for the initialization request
            message = self.socket.recv()
            if message == b"ping":
                # If the message is not a ping then it doesn't count as successful
                self.connected = True
                self.socket.send(b"pong")

                # Reset this to be infinite amount of time
                self.socket.set(zmq.RCVTIMEO, -1)
            else:
                print(f"Received unexpected connection request: {message}")
        except Again:
            pass

        # Continue the connection by listening
        if self.connected:
            self.__receiver()

    def __receiver(self):
        while True:
            #  Wait for next request from client
            message = self.socket.recv()

            if message == b"ping":
                self.socket.send(b"pong")

    def send(self, message: str):
        self.socket.send(message.encode('ascii'))
