import thread, json, time, Utils
from websocket import create_connection

class Tickers:
    def __init__(self, coinID, log="", show=False, WEBSOCKET_URL="wss://ws-feed.pro.coinbase.com"):
        self.__id = coinID
        if (len(log) > 1):
            self.__log = True
            self.__filePath = log
            try:
                self.__file = open(log, 'xa')
                self.__file.write(
                    "time,system_time,price,open_24h,volume_24h,low_24h,high_24h,volume_30d,best_bid,best_ask,last_size\n")
            except:
                self.__file = open(log, 'a')
        else:
            self.__log = False

        self.__webSocketClosed = False
        ws = self.createTickerConnection(coinID, WEBSOCKET_URL)
        self.__response = ws.recv()
        self.__show = show
        thread.start_new_thread(self.readWebsocket, (ws,))
        self.__tickerFeed = []
        self.__timeFeed = []
        self.__websocket = ws
        self.__utils = Utils.Utils()
        self.__mostRecentTick = None
        self.__managers = []

    def createTickerConnection(self, id, url):
        ws = create_connection(url)
        request = """{
        "type": "subscribe",
        "product_ids": [
            \"""" + id + """\"
        ],
        "channels": [
            {
                "name": "ticker",
                "product_ids": [
                    \"""" + id + """\"
                ]
            }
        ]
        }"""
        ws.send(request)
        return ws

    def closeWebSocket(self):
        self.__webSocketClosed = True
        print "Closed websocket for " + self.__id

    def readWebsocket(self, ws):
        counter = 0
        try:
            while not self.__webSocketClosed:
                receivedString = ws.recv()
                received = json.loads(receivedString)
                if self.__show:
                    print received
                if self.__log:
                    if (counter % 100 == 0):
                        self.__file.close()
                        self.__file = open(self.__filePath, 'a')
                    line = received["time"] + "," + str(time.time()) + "," + received["price"] + "," + received["open_24h"] + "," + received["volume_24h"] + "," + received["low_24h"] + "," + received["high_24h"] + "," + received["volume_30d"] + "," + received["best_bid"] + "," + received["best_ask"] + "," + received["last_size"] + "\n"
                    self.__file.write(line)
                    print(receivedString)
                self.__tickerFeed.append(received)
                self.__mostRecentTick = received

                # Manage price events and fire for each manager attached
                for i in range(len(self.__managers)):
                    self.__managers[i].priceEvent(self.__mostRecentTick)

                self.__timeFeed.append(self.__utils.getEpochFromISO8601(received["time"]))
                counter += 1
        except Exception("websocket._exceptions.WebSocketConnectionClosedException") as e:
            print("Error reading websocket")
        ws.close()
        print("websocket closed")

    def isWebsocketOpen(self):
        return not self.__webSocketClosed

    """ Parallel with time feed """
    def getTickerFeed(self):
        return self.__tickerFeed

    def getTimeFeed(self):
        return self.__timeFeed

    """ Define a variable each time so there is no array manipulation """
    def getMostRecentTick(self):
        return self.__mostRecentTick

    def getMostRecentTime(self):
        return self.__timeFeed[-1]

    def getResponse(self):
        return self.__response

    def updateShow(self, value):
        self.__show = value

    def addSelfToTicker(self, obj):
        self.__managers.append(obj)

    def getCoinID(self):
        return self.__id
