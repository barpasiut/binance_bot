import numpy as np
import datetime
import sys

class Data:

    LAST_ON_LIST = -1
    TEST_FILENAME = "dataTest.txt"
    DATA_THRESHOLD_BUY = 0.00085
    DATA_THRESHOLD_SELL = 0.0005
    MAX_PRICES_LIST_COUNT = 26
    
    def __init__(self):
        self.__lastAskList = []
        self.__lastBidList = []

        self.__avgLastAskList = []
        self.__avgLastBidList = []
        
        self.__pricesList = []
        
        self.__maCounter = 0
        self.__rsiFactor = 0
        self.__signalFactors = [0] * 9
        self.__MACDFactors = []
        self.__EMA26Factors = []
        self.__EMA12Factors = []
        self.__EMA9FactorsFromSubtr = []
        
        self.__raiseFallAskFactor = 0
        self.__raiseFallBidFactor = 0

        self.__maxRaiseFallAskFactor = sys.float_info.min
        self.__maxRaiseFallBidFactor = sys.float_info.min
        self.__maxRaiseFallAskFactorDatetime = ""
        self.__maxRaiseFallBidFactorDatetime = ""
        
        self.__minRaiseFallAskFactor = sys.float_info.max
        self.__minRaiseFallBidFactor = sys.float_info.max
        self.__minRaiseFallAskFactorDatetime = ""
        self.__minRaiseFallBidFactorDatetime = ""

    def __sma(self, data, window):
        if len(data) < window:
            return None
        return sum(data) / float(window)
    
    def __ema(self, data, window):
        if len(data) < 2 * window:
            raise ValueError("data is to short")
        c = 2.0 / (window + 1)
        current_ema = self.__sma(data[window:window*2], window)
        for value in data[window:window*2]:
            current_ema = (c * value) + ((1 - c) * current_ema)
        return current_ema
    
    def __comMACD(self, candles):
        self.__EMA12Factors = self.__ExpMovingAverage(candles, 12)#self.__ema(candles, 12)
        self.__EMA26Factors = self.__ExpMovingAverage(candles, 26)#self.__ema(candles, 26)
        self.__MACDFactors = self.__EMA12Factors - self.__EMA26Factors
        self.__signalFactors = self.__ExpMovingAverage(self.__MACDFactors, 9)
        
    def __ExpMovingAverage(self, values, window):
        """ Numpy implementation of EMA
        """
        weights = np.exp(np.linspace(-1., 0., window))
        weights /= weights.sum()
        a =  np.convolve(values, weights, mode='full')[:len(values)]
        a[:window] = a[window]
        return a
        
    def __calculate_ema(self, candles, emaList):
        length = len(emaList)
        sumCand = sum(candles[-length:-1]) + candles[-1]
        emaListHelper = emaList
        emaList.clear()
        emaList.append(sumCand / length)
        multipler = 2 / (length + 1)
        for i in range(length - 1):
            emaList.append((candles[-length+1+i] * multipler) + (emaList[0] * (1 - multipler)))
        
    def __calculate_ema26(self, candles):
        self.__calculate_ema(candles, self.__EMA26Factors)

    def __calculate_ema12(self, candles):
        self.__calculate_ema(candles, self.__EMA12Factors)
    
    def __calculate_ema9FromSubtr(self):
        self.__calculate_ema(self.__MACDFactors, self.__EMA9FactorsFromSubtr)
        
    def __computeMACD(self, candles):
        self.__calculate_ema12(candles)
        self.__calculate_ema26(candles)

        self.__MACDFactors.append((self.__EMA12Factors[-1] - self.__EMA26Factors[-1]))# = [(self.__EMA12Factors[i] - self.__EMA26Factors[i]) for i in range(len(self.__EMA12Factors))]
        self.__calculate_ema9FromSubtr()
        
    '''
    def __computeMA(self, lastVal):
        self.__MA26Factor = (np.mean(self.__pricesList[:self.MAX_PRICES_LIST_COUNT]) / lastVal) - 1
        self.__MA12Factor = (np.mean(self.__pricesList[:int(self.MAX_PRICES_LIST_COUNT / 2 - 1)]) / lastVal) - 1
    
    def __computeMACD(self):
        return self.__MA12Factor - self.__MA26Factor
    '''
    def __rsiFunc(self, prices):
        deltas = np.diff(prices)
        seed = deltas[:self.MAX_PRICES_LIST_COUNT+1]
        up = seed[seed>=0].sum()/self.MAX_PRICES_LIST_COUNT
        down = -seed[seed<0].sum()/self.MAX_PRICES_LIST_COUNT
        rs = up/down
        rsi = np.zeros_like(prices)
        rsi[:self.MAX_PRICES_LIST_COUNT] = 100. - 100./(1.+rs)

        for i in range(self.MAX_PRICES_LIST_COUNT, len(prices)):
            delta = deltas[i-1] # cause the diff is 1 shorter

            if delta>0:
                upval = delta
                downval = 0.
            else:
                upval = 0.
                downval = -delta

            up = (up*(n-1) + upval)/self.MAX_PRICES_LIST_COUNT
            down = (down*(n-1) + downval)/self.MAX_PRICES_LIST_COUNT

            rs = up/down
            rsi[i] = 100. - 100./(1.+rs)

        return rsi
    
    def __updateList(self, lastVal, lastList, maxLastListCount):
        if len(lastList) == maxLastListCount:
            lastList.pop(0)
            
        lastList.append(float(lastVal))
    
    def __updateAskOrBidLists(self, lastVal, lastList, avgLastList, maxLastListCount, maxAvgLastListCount):
        if len(lastList) == maxLastListCount:
            lastList.pop(0)
            
        lastList.append(float(lastVal))
        
        if len(avgLastList) == maxAvgLastListCount:
            avgLastList.pop(0)
            
        avgLastList.append(np.mean(lastList))
    
    def getRaiseFallAskFactor(self):
        return self.__raiseFallAskFactor
    
    def getRaiseFallBidFactor(self):
        return self.__raiseFallBidFactor
    
    def updateMACDFactor(self, candles):
        self.__comMACD(candles)
        
        print("\n")
        #print("EMA26 Factors: {}".format(self.__EMA26Factors))
        #print("EMA12 Factors: {}".format(self.__EMA12Factors))
        print("MACD Factors: {}".format(self.__MACDFactors))
        print("Signal Factors: {}".format(self.__signalFactors))
        print("MACD - Signal Factors: {}".format([(self.__MACDFactors[i] - self.__signalFactors[i]) for i in range(len(self.__signalFactors))]))
    
    def updateAskAndBidData(self, msg, maxLastListCount, maxAvgLastListCount):
        #self.__updateList(msg['c'], self.__pricesList, self.MAX_PRICES_LIST_COUNT)
        
        #self.__maCounter = self.__maCounter + 1
        #self.__rsiFactor = self.__rsiFunc(self.__pricesList)
        #if len(self.__pricesList) == self.MAX_PRICES_LIST_COUNT: #and self.__maCounter == 60:
            #self.__computeMA(float(msg['c']))
            #self.__maCounter = 0
            #self.__computeMACD(self.__pricesList)
        
        self.__updateAskOrBidLists(msg['a'], self.__lastAskList, self.__avgLastAskList, maxLastListCount, maxAvgLastListCount)
        self.__updateAskOrBidLists(msg['b'], self.__lastBidList, self.__avgLastBidList, maxLastListCount, maxAvgLastListCount)

        '''
        self.__raiseFallAskFactor = self.__avgLastAskList[self.LAST_ON_LIST] / np.mean(self.__avgLastAskList)
        self.__raiseFallBidFactor = self.__avgLastBidList[self.LAST_ON_LIST] / np.mean(self.__avgLastBidList)
        '''
        
        maxRaiseFallAsk = max(self.__avgLastAskList)
        minRaiseFallAsk = min(self.__avgLastAskList)
        maxRaiseFallBid = max(self.__avgLastBidList)
        minRaiseFallBid = min(self.__avgLastBidList)
        
        if self.__avgLastAskList.index(maxRaiseFallAsk) >= self.__avgLastAskList.index(minRaiseFallAsk):
            self.__raiseFallAskFactor = (maxRaiseFallAsk - minRaiseFallAsk) / minRaiseFallAsk
        else:
            self.__raiseFallAskFactor = (minRaiseFallAsk - maxRaiseFallAsk) / maxRaiseFallAsk
         
        if self.__avgLastBidList.index(maxRaiseFallBid) >= self.__avgLastBidList.index(minRaiseFallBid):
            self.__raiseFallBidFactor = (maxRaiseFallBid - minRaiseFallBid) / minRaiseFallBid
        else:
            self.__raiseFallBidFactor = (minRaiseFallBid - maxRaiseFallBid) / maxRaiseFallBid
        
        if self.__maxRaiseFallAskFactor < self.__raiseFallAskFactor:
            self.__maxRaiseFallAskFactor = self.__raiseFallAskFactor
            self.__maxRaiseFallAskFactorDatetime = datetime.datetime.now().time().strftime("%H:%M:%S\n")
        elif self.__minRaiseFallAskFactor > self.__raiseFallAskFactor:
            self.__minRaiseFallAskFactor = self.__raiseFallAskFactor
            self.__minRaiseFallAskFactorDatetime = datetime.datetime.now().time().strftime("%H:%M:%S\n")
            
        if self.__maxRaiseFallBidFactor < self.__raiseFallBidFactor:
            self.__maxRaiseFallBidFactor = self.__raiseFallBidFactor
            self.__maxRaiseFallBidFactorDatetime = datetime.datetime.now().time().strftime("%H:%M:%S\n")
        elif self.__minRaiseFallBidFactor > self.__raiseFallBidFactor:
            self.__minRaiseFallBidFactor = self.__raiseFallBidFactor
            self.__minRaiseFallBidFactorDatetime = datetime.datetime.now().time().strftime("%H:%M:%S\n")
    
    def print(self):
        print("Last Ask List: {}".format(self.__lastAskList))
        print("Last Bid List: {}".format(self.__lastBidList))
        
        print("Average Last Ask List: {}".format(self.__avgLastAskList))
        print("Average Last Bid List: {}".format(self.__avgLastBidList))
        
        print("Raise Fall Ask Factor: {}".format(self.__raiseFallAskFactor))
        print("Max/Min Raise Fall Ask Factor: {}/{}".format(self.__maxRaiseFallAskFactor, self.__minRaiseFallAskFactor))
        print("Max/Min Raise Fall Ask Factor Datetime: {}/{}".format(self.__maxRaiseFallAskFactorDatetime, self.__minRaiseFallAskFactorDatetime))
        print("Raise Fall Bid Factor: {}".format(self.__raiseFallBidFactor))
        print("Max/Min Raise Fall Bid Factor: {}/{}".format(self.__maxRaiseFallBidFactor, self.__minRaiseFallBidFactor))
        print("Max/Min Raise Fall Bid Factor Datetime: {}/{}".format(self.__maxRaiseFallBidFactorDatetime, self.__minRaiseFallBidFactorDatetime))
        print("\n")
        
        if self.__raiseFallBidFactor > self.DATA_THRESHOLD_SELL:
            file = open(self.TEST_FILENAME, 'a')
            strToWrite = datetime.datetime.now().time().strftime("%H:%M:%S\n") + " RaiseFallBidFactor is big: " + str(self.__raiseFallBidFactor) + "\n"
            file.write(strToWrite)
            file.close()
        if self.__raiseFallAskFactor < -self.DATA_THRESHOLD_BUY:
            file = open(self.TEST_FILENAME, 'a')
            strToWrite = datetime.datetime.now().time().strftime("%H:%M:%S\n") + " RaiseFallAskFactor is small: " + str(self.__raiseFallAskFactor) + "\n"
            file.write(strToWrite)
            file.close()
        
