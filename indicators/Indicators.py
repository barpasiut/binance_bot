from stockstats import StockDataFrame
import pandas as pd

class IndicatorSymbol:
    
    MACD = 1
    RSI_12 = 2
    BOLL = 3

class Indicators:
    
    def __init__(self):
        self.__data = pd.DataFrame()
    
    def __updateData(self, data):
        self.__data = pd.DataFrame(data,columns=['low','high','open','close'])
        cols = self.__data.select_dtypes(exclude=['float']).columns
        self.__data[cols] = self.__data[cols].apply(pd.to_numeric, downcast='float', errors='coerce')
        self.__data = StockDataFrame.retype(self.__data)
    
    def calculate(self, data, *inds):    
        self.__updateData(data)
        if len(inds) > 3:
            raise Exception("To many args for Indicator calculate funtion") 
        for ind in inds:
            if ind == IndicatorSymbol.MACD:
                self.__data['macd'] = self.__data.get('macd')
            elif ind == IndicatorSymbol.RSI_12:
                self.__data['rsi_12'] = self.__data.get('rsi_12')
            elif ind == IndicatorSymbol.BOLL:
                self.__data['boll'] = self.__data.get('boll')
        
    def getMacd(self):
        return self.__data['macd']
    
    def getMacds(self):
        return self.__data['macds']
    
    def getMacdh(self):
        return self.__data['macdh']
    
    def getMacdAll(self):
        return self.__data[['macd','macds','macdh']]
    
    def getRsi(self):
        return self.data['rsi_12']
    
    def getRsi(self):
        return self.data['boll']
    
    def getAllIndicators(self):
        # not all but still ok
        return self.__data[['macd','macds','macdh','rsi_12','boll']]
