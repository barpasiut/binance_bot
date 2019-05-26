from binance.websockets import BinanceSocketManager

class Streams:

    WEBSOCKET_TIMEOUT = 5000

    def __init__(self, client):
        self.__socketManager = BinanceSocketManager(client, user_timeout = self.WEBSOCKET_TIMEOUT)

    def getUserData(self, callback):
        self.__socketManager.start_user_socket(callback)
        
    def getSymbolTicker(self, symbol, callback):
        self.__socketManager.start_symbol_ticker_socket(symbol, callback)
        
    def getSymbolKline(self, symbol, callback):
        self.__socketManager.start_kline_socket(symbol, callback)
        
    def startSocketManager(self):
        self.__socketManager.start()
