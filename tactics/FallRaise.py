from tactics.Data import Data
from binance.client import Client
from connection.Filters import Filters
from simulator.FallRaiseSim import FallRaiseSim

class FallRaise:
    
    SYMBOL = "BTCUSDT"
    MAX_LAST_LIST_COUNT = 8
    MAX_AVG_LAST_LIST_COUNT = 8
    COUNT_FALL_RAISE_NUMBERS = 6
    COUNT_TIME_FALL_RAISE_NUMBERS = 4
    ADJUST_OFFER = 0.05
    KNILE_INTERVAL_STR = "54 minutes ago UTC"

    def __init__(self, streams, client):
        self.__data = Data()
        self.__client = client
        self.__filters = Filters(client, self.SYMBOL).getFilters()
        self.__sim = FallRaiseSim(self.__client, self.__filters)
        
        self.__countAskFall = 0
        self.__countAskRaise = 0
        self.__countBidRaise = 0
        self.__countBidFall = 0
        self.__histKnile26List = []
        
        self.__buyingState = False
        self.__sellingState = False
        
        streams.getSymbolTicker(self.SYMBOL, self.handleSymbolTickerData)
        streams.getSymbolKline(self.SYMBOL, self.handleSymbolKlineData)
        streams.startSocketManager()
        
    def __updateSymbolTickerData(self, msg):
        self.__data.updateAskAndBidData(msg, self.MAX_LAST_LIST_COUNT, self.MAX_AVG_LAST_LIST_COUNT)
    
    def __updateSymbolKlineData(self, klineData):
        self.__data.updateMACDFactor(klineData)
    
    def handleSymbolTickerData(self, msg):
        if msg['e'] == "error":
            print("Error occured!")
            print("Error message: {}".format(msg['m']))
        #else:
            #print("Best ask: {}".format(msg['a']))
            #print("Best bid: {}".format(msg['b']))
            
        self.__updateSymbolTickerData(msg)
        
        if self.__buyingState == True:
            strToWrite = "BuyingState with raise fall ask factor: {}\n".format(self.__data.getRaiseFallAskFactor())
            if self.__data.getRaiseFallAskFactor() > 0:
                self.__countAskRaise = self.__countAskRaise + 1
                strToWrite = "BuyingState countAskRaise incrementation {}\n".format(self.__countAskRaise)
                if self.__countAskRaise == self.COUNT_TIME_FALL_RAISE_NUMBERS:
                    self.__sim.makeTrade(True, round(float(msg['a']) + self.ADJUST_OFFER, 2))
                    self.__buyingState = False
                    self.__countAskRaise = 0
                    strToWrite = "BuyingState change to false"
            else:
                self.__countAskRaise = 0
            file = open(self.__data.TEST_FILENAME, 'a')
            file.write(strToWrite)
            file.close()
        elif self.__data.getRaiseFallAskFactor() < -self.__data.DATA_THRESHOLD_BUY:
            self.__countAskFall = self.__countAskFall + 1
            file = open(self.__data.TEST_FILENAME, 'a')
            strToWrite = "Count ask fall incremented. Current count ask: {}\n".format(self.__countAskFall)
            file.write(strToWrite)
            file.close()
            if(self.__countAskFall == self.COUNT_FALL_RAISE_NUMBERS):
                self.__buyingState = True     
        else:
            self.__countAskFall = 0

        if self.__sellingState == True:
            strToWrite = "SellingState with raise fall bid factor: {}\n".format(self.__data.getRaiseFallBidFactor())
            if self.__data.getRaiseFallBidFactor() < 0:
                strToWrite = "SellingState countBidFall incrementation {}\n".format(self.__countBidFall)
                self.__countBidFall = self.__countBidFall + 1
                if self.__countBidFall == self.COUNT_TIME_FALL_RAISE_NUMBERS:
                    self.__sim.makeTrade(False, round(float(msg['b']) - self.ADJUST_OFFER, 2))
                    self.__sellingState = False
                    self.__countBidFall = 0
                    strToWrite = "SellingState change to false"
            else:
                self.__countBidFall = 0
            file = open(self.__data.TEST_FILENAME, 'a')
            file.write(strToWrite)
            file.close()
        elif self.__data.getRaiseFallBidFactor() > self.__data.DATA_THRESHOLD_SELL:
            self.__countBidRaise = self.__countBidRaise + 1
            file = open(self.__data.TEST_FILENAME, 'a')
            strToWrite = "Count bid fall incremented. Current count bid: {}\n".format(self.__countBidRaise)
            file.write(strToWrite)
            file.close()
            if(self.__countBidRaise == self.COUNT_FALL_RAISE_NUMBERS):
                self.__sellingState = True
        else:
            self.__countBidRaise = 0

        #self.__data.print()
        
    def handleSymbolKlineData(self, msg):
        if msg['e'] == "error":
            print("Error occured!")
            print("Error message: {}".format(msg['m']))
        #else:
            #print("Event time: {}".format(msg['E']))
            #print("CLOSE: {}".format(msg['k']['c']))
            #print("Close time: {}".format(msg['k']['T']))
             
        klineData = [float(el[4]) for el in self.__client.get_historical_klines(self.SYMBOL, Client.KLINE_INTERVAL_1MINUTE, self.KNILE_INTERVAL_STR)]
        self.__updateSymbolKlineData(klineData)
            