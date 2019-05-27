import datetime
import math
import time
import random
from binance.client import Client
from connection.Connection import Connection
from indicators.Indicators import *

class MacdAndRsi:

    MARKET_DIRECTION_DOWN = "DOWN"
    MARKET_DIRECTION_UP = "UP"
    MARKET_DIRECTION_UNKNOWN = "UNKNOWN"
    MARKET_DIRECTION_UP_DECISION_TREESHOLD = 0.003
    
    BUY_STATE = "BUY"
    SELL_STATE = "SELL"
    WAIT_BUY_STATE = "WAIT_BUY"
    WAIT_SELL_STATE = "WAIT_SELL"
    
    SYMBOL_BTC = "BTCUSDT"
    SYMBOL_ETH = "ETHUSDT"
    SYMBOL_LTC = "LTCUSDT"
    SYMBOL_BNB = "BNBUSDT"
    
    STOP_LOSS_IND = 0.9
    STOP_GAIN_IND = 1.0025
    
    KNILE_1M_INTERVAL_STR = "54 minutes ago UTC"
    KNILE_3M_INTERVAL_STR = "162 minutes ago UTC"
    MARKET_DOWN_MACD_1M_BUY_DECISION_TREESHOLD = 0
    MARKET_UP_MACD_1M_SELL_DECISION_TREESHOLD = 15
    MARKET_MACD_1M_SELL_DECISION_TREESHOLD = 20
    MARKET_MACDH_1M_BUY_DECISION_TREESHOLD = 0
    MARKET_MACDH_1M_SELL_DECISION_TREESHOLD = 5
    MACD_3M_BUY_DECISION_TREESHOLD = 0
    MACD_3M_SELL_DECISION_TREESHOLD = 0
    RSI_1M_BUY_DECISION_TREESHOLD = 50
    RSI_1M_SELL_DECISION_TREESHOLD = 70
    BOLLINGER_LINE_DECISION_TREESHOLD = 10
    
    WAIT_BEFORE_CANCEL_TIME = 60 #in sec
    
    BALANCES_INF = {SYMBOL_BTC:0}#, SYMBOL_ETH:2}# , SYMBOL_LTC:1, SYMBOL_BNB:4}
    FLOOR_IND = {SYMBOL_BTC:1000000}#, SYMBOL_ETH:100000}#, SYMBOL_LTC:100000, SYMBOL_BNB:100}

    def __init__(self):
        self.__market_direction = {self.SYMBOL_BTC:self.MARKET_DIRECTION_UNKNOWN}#, self.SYMBOL_ETH:self.MARKET_DIRECTION_UNKNOWN}, self.SYMBOL_LTC:self.MARKET_DIRECTION_UNKNOWN, self.SYMBOL_BNB:self.MARKET_DIRECTION_UNKNOWN}
        
        self.__state = self.BUY_STATE
        self.__buySymCoin = self.SYMBOL_BTC
        self.__sellSymCoin = self.SYMBOL_BTC
        self.__rsi_1m_buy = True
        self.__rsi_1m_sell = True
        self.__buyStateIsSet = False
        self.__buyStateIsSetDownCounter = 0
        
        self.conn = Connection()
        self.indic = Indicators()
        self.conn.streams.getSymbolKline(self.SYMBOL_BTC, self.__handleKlineChanges)
        #self.conn.streams.getSymbolKline(self.SYMBOL_ETH, self.__handleKlineChanges)
        #self.conn.streams.getSymbolKline(self.SYMBOL_LTC, self.__handleKlineChanges)
        #self.conn.streams.getSymbolKline(self.SYMBOL_BNB, self.__handleKlineChanges)
        #depreciated method because of network delays
        #self.conn.streams.getUserData(self.__handleOrdersChanges)
        self.conn.streams.startSocketManager()
        print("STATE: {}".format(self.__state))
        
    def __parseHistoricalKlines(self, symbol, interval, intervalStr):
        data = self.conn.client.get_historical_klines(symbol, interval, intervalStr)
        data = [k[1:5] for k in data]
        return data
     
    
    def __handleOrdersChanges(self, msg):
        if msg['e'] == "executionReport":
            if msg['X'] == Client.ORDER_STATUS_NEW:
                self.__state = self.WAIT_STATE
            elif msg['X'] == Client.ORDER_STATUS_CANCELED:
                if msg['S'] == Client.SIDE_BUY:
                    self.__state = self.BUY_STATE
                elif msg['S'] == Client.SIDE_SELL:
                    self.__state = self.SELL_STATE
            elif msg['X'] == Client.ORDER_STATUS_FILLED:
                if msg['S'] == Client.SIDE_BUY:
                    self.__state = self.SELL_STATE
                elif msg['S'] == Client.SIDE_SELL:
                    self.__state = self.BUY_STATE
            print("STATE: {}".format(self.__state))
        
    def __handleKlineChanges(self, msg):
        if msg['e'] == "error":
            raise Exception(msg['m'])
            
        if self.__state == self.WAIT_BUY_STATE:
            if not self.conn.client.get_open_orders(symbol=self.__buySymCoin):
                self.__state = self.SELL_STATE
                print("STATE: {}".format(self.__state))
            elif time.time() - self.WAIT_BEFORE_CANCEL_TIME > self.conn.orders.getBuyOrderTime():
                self.conn.client.cancel_order(symbol=self.__buySymCoin, orderId=self.conn.orders.getCurrentOrderId())
                self.__state = self.BUY_STATE
                print("STATE: {}".format(self.__state))
        elif self.__state == self.WAIT_SELL_STATE:
            if not self.conn.client.get_open_orders(symbol=self.__buySymCoin):
                self.__state = self.BUY_STATE
                print("STATE: {}".format(self.__state))
            elif time.time() - self.WAIT_BEFORE_CANCEL_TIME > self.conn.orders.getSellOrderTime():
                self.conn.client.cancel_order(symbol=self.__buySymCoin, orderId=self.conn.orders.getCurrentOrderId())
                self.__state = self.SELL_STATE
                print("STATE: {}".format(self.__state))
        else:
            data1m = self.__parseHistoricalKlines(msg['s'], Client.KLINE_INTERVAL_1MINUTE, self.KNILE_1M_INTERVAL_STR)
            self.indic.calculate(data1m, IndicatorSymbol.MACD, IndicatorSymbol.RSI_12, IndicatorSymbol.BOLL)
            indic1m = self.indic.getAllIndicators()

            data3m = self.__parseHistoricalKlines(msg['s'], Client.KLINE_INTERVAL_3MINUTE, self.KNILE_3M_INTERVAL_STR)
            self.indic.calculate(data3m, IndicatorSymbol.MACD, IndicatorSymbol.RSI_12, IndicatorSymbol.BOLL)
            indic3m = self.indic.getAllIndicators()

            self.__calculateMarketDirection(msg['s'], indic3m)
            self.__makeDecision(float(msg['k']['c']), msg['s'], indic1m, indic3m)
    
    def __calculateMarketDirection(self, symbol, indic3m):
        boll30Avg = sum(indic3m['boll'][-15:])/15
        bollInd = (indic3m['boll'].iloc[-1] - boll30Avg) / indic3m['boll'].iloc[-1]
        if bollInd >= self.MARKET_DIRECTION_UP_DECISION_TREESHOLD:
            self.__market_direction[symbol] = self.MARKET_DIRECTION_UP
        elif bollInd >= 0:
            self.__market_direction[symbol] = self.MARKET_DIRECTION_UNKNOWN
        elif bollInd < 0:
            self.__market_direction[symbol] = self.MARKET_DIRECTION_DOWN
        print("Symbol {}, bollInd {}, market_dir: {}".format(symbol, bollInd, self.__market_direction[symbol]))
    
    def __makeDecision(self, price, symbol, indic1m, indic3m):
        if self.__market_direction[symbol] == self.MARKET_DIRECTION_UP:
            rsi1mBuyDecisionTreeshold = self.RSI_1M_BUY_DECISION_TREESHOLD
            rsi1mSellDecisionTreeshold = self.RSI_1M_SELL_DECISION_TREESHOLD + self.BOLLINGER_LINE_DECISION_TREESHOLD
        elif self.__market_direction[symbol] == self.MARKET_DIRECTION_UNKNOWN:
            rsi1mBuyDecisionTreeshold = self.RSI_1M_BUY_DECISION_TREESHOLD
            rsi1mSellDecisionTreeshold = self.RSI_1M_SELL_DECISION_TREESHOLD
        elif self.__market_direction[symbol] == self.MARKET_DIRECTION_DOWN:
            rsi1mBuyDecisionTreeshold = self.RSI_1M_BUY_DECISION_TREESHOLD - self.BOLLINGER_LINE_DECISION_TREESHOLD
            rsi1mSellDecisionTreeshold = self.RSI_1M_SELL_DECISION_TREESHOLD - self.BOLLINGER_LINE_DECISION_TREESHOLD
        print("Symbol {}, RsiBuy {}, RsiSell: {}".format(symbol, rsi1mBuyDecisionTreeshold, rsi1mSellDecisionTreeshold))
            
        if self.__state == self.BUY_STATE:
            self.__makeBuyDecision(price, symbol, indic1m, indic3m, rsi1mBuyDecisionTreeshold)
        elif self.__state == self.SELL_STATE and self.__buySymCoin == symbol:
            #self.__makeSellDecision(indic1m, indic3m, rsi1mSellDecisionTreeshold)
            self.__makeSellDecision(price, indic1m)
    
    def __buyProcess(self, symbol):
        print("BUY in {}".format(datetime.datetime.now().time().strftime("%H:%M:%S\n")))
        self.__state = self.WAIT_BUY_STATE
        self.__buySymCoin = symbol
        curr = float(self.conn.client.get_account()['balances'][11]['free'])
        price = float(self.conn.client.get_orderbook_ticker(symbol=symbol)['bidPrice'])
        amount = math.floor((curr/price)*self.FLOOR_IND[symbol])/self.FLOOR_IND[symbol]
        self.conn.orders.makerBuy(self.conn.client, symbol, amount, price)
        print("BOUGHT:\n Symbol: {}\n Curr: {}\n Price: {}\n Amount: {}\nSTATE: {}\n".format(symbol, curr, price, amount, self.__state))
    
    def __sellProcess(self):
        print("SELL in {}".format(datetime.datetime.now().time().strftime("%H:%M:%S\n")))
        self.__state = self.WAIT_SELL_STATE
        amount = math.floor(float(self.conn.client.get_account()['balances'][self.BALANCES_INF[self.__buySymCoin]]['free'])*self.FLOOR_IND[self.__buySymCoin])/self.FLOOR_IND[self.__buySymCoin]
        price = float(self.conn.client.get_orderbook_ticker(symbol=self.__buySymCoin)['askPrice'])
        self.conn.orders.makerSell(self.conn.client, self.__buySymCoin, amount, price)
        print("SOLD:\n Symbol: {}\n Price: {}\n Amount: {}\nSTATE: {}\n".format(self.__buySymCoin, price, amount, self.__state))
        
    def __makeBuyDecision(self, price, symbol, indic1m, indic3m, rsiTreeshold):
        if indic1m['macd'].iloc[-1] < self.MARKET_DOWN_MACD_1M_BUY_DECISION_TREESHOLD and indic1m['macdh'].iloc[-2] < self.MARKET_MACDH_1M_BUY_DECISION_TREESHOLD and indic1m['macdh'].iloc[-1] > self.MARKET_MACDH_1M_BUY_DECISION_TREESHOLD and indic1m['rsi_12'].iloc[-1] < self.RSI_1M_BUY_DECISION_TREESHOLD:
            for macdh in indic1m['macdh'][-7:-1]:
                if macdh > 0:
                    return
            ticker = self.conn.client.get_ticker(symbol=symbol)
            prob = (1 - (price - float(ticker['lowPrice']))/ (float(ticker['highPrice']) - float(ticker['lowPrice']))) * (1 + abs(indic1m['macd'].iloc[-1]) / 100)
            print("IN MAKE BUY DECISION FIRST IF: prob={}".format(prob))
            if self.__buyIsSet(prob):
                print("IN MAKE BUY DECISION SECOND IF: prob={}".format(prob))
                self.__buyProcess(symbol)

        '''
        if indic1m['macd'].iloc[-1] < self.MARKET_DOWN_MACD_1M_BUY_DECISION_TREESHOLD and indic1m['macdh'].iloc[-1] < self.MARKET_MACDH_1M_BUY_DECISION_TREESHOLD and indic1m['macdh'].iloc[-1] > indic1m['macdh'].iloc[-2]:
            self.__buyProcess(symbol)
        
        elif self.__market_direction[symbol] == self.MARKET_DIRECTION_DOWN:
            
            if indic1m['macd'].iloc[-1] < self.MARKET_DOWN_MACD_1M_BUY_DECISION_TREESHOLD and indic1m['macdh'].iloc[-1] > 0:
                self.__buyProcess(symbol)
        elif self.__market_direction[symbol] == self.MARKET_DIRECTION_UP or self.__market_direction[symbol] == self.MARKET_DIRECTION_UNKNOWN:
            if indic1m['rsi_12'].iloc[-2] < rsiTreeshold:
                self.__rsi_1m_buy = True

            if self.__rsi_1m_buy == True and indic1m['rsi_12'].iloc[-2] > rsiTreeshold:
                self.__rsi_1m_buy = False

                if indic3m['macdh'].iloc[-1] < self.MACD_3M_BUY_DECISION_TREESHOLD:
                    self.__buyProcess(symbol)
        '''
    def __makeSellDecision(self, price, indic1m):
        if price < self.conn.orders.getBuyPrice() * self.STOP_LOSS_IND:
            self.__sellProcess()
            self.__buyStateIsSet = False
            self.__buyStateIsSetDownCounter = 0
        elif price > self.conn.orders.getBuyPrice() * self.STOP_GAIN_IND:
            print("BEFORE self.__buyStateIsSet = True:\n self.__buyStateIsSet: {}\n self.__buyStateIsSetDownCounter: {}\n price: {}\n".format(self.__buyStateIsSet, self.__buyStateIsSetDownCounter, price))
            if(self.__buyStateIsSet == False):
                time.sleep(60)
            self.__buyStateIsSet = True
            self.__buyStateIsSetDownCounter = 0
            
            if indic1m['macd'].iloc[-1] < indic1m['macd'].iloc[-2]:
                print("BEFORE SELL PROCESS IN PRICE COND:\n self.__buyStateIsSet: {}\n self.__buyStateIsSetDownCounter: {}\n price: {}\n".format(self.__buyStateIsSet, self.__buyStateIsSetDownCounter, price))
                self.__sellProcess()
                print("AFTER SELL PROCESS IN PRICE COND:\n self.__buyStateIsSet: {}\n self.__buyStateIsSetDownCounter: {}\n price: {}\n".format(self.__buyStateIsSet, self.__buyStateIsSetDownCounter, price))
                self.__buyStateIsSet = False
        else:
            if self.__buyStateIsSet == True:
                print("BEFORE self.__buyStateIsSetDownCounter:\n self.__buyStateIsSet: {}\n self.__buyStateIsSetDownCounter: {}\n price: {}\n".format(self.__buyStateIsSet, self.__buyStateIsSetDownCounter, price))
                self.__buyStateIsSetDownCounter = self.__buyStateIsSetDownCounter + 1
                if self.__buyStateIsSetDownCounter == 8:
                    print("BEFORE SELL PROCESS IN BACKUP COND:\n self.__buyStateIsSet: {}\n self.__buyStateIsSetDownCounter: {}\n price: {}:\n".format(self.__buyStateIsSet, self.__buyStateIsSetDownCounter, price))
                    self.__sellProcess()
                    print("AFTER SELL PROCESS IN BACKUP COND:\n self.__buyStateIsSet: {}\n self.__buyStateIsSetDownCounter: {}\n price: {}\n".format(self.__buyStateIsSet, self.__buyStateIsSetDownCounter, price))
                    self.__buyStateIsSet = False

        '''
    def __makeSellDecision(self, indic1m, indic3m, rsiTreeshold):
        if indic1m['macd'].iloc[-1] > self.MARKET_UP_MACD_1M_SELL_DECISION_TREESHOLD and indic1m['macdh'].iloc[-1] > self.MARKET_MACDH_1M_SELL_DECISION_TREESHOLD and indic1m['macdh'].iloc[-1] < indic1m['macdh'].iloc[-2]:
            self.__sellProcess()
        
        if self.__rsi_1m_sell == False and indic1m['macd'].iloc[-1] > self.MARKET_MACD_1M_SELL_DECISION_TREESHOLD and indic1m['macdh'].iloc[-1] < 0:
            self.__sellProcess()
        
        elif indic1m['rsi_12'].iloc[-1] > rsiTreeshold:
            self.__rsi_1m_sell = True
        
        if self.__rsi_1m_sell == True and indic1m['rsi_12'].iloc[-1] < rsiTreeshold:
            self.__rsi_1m_sell = False
            
            if indic3m['macdh'].iloc[-1] > self.MACD_3M_SELL_DECISION_TREESHOLD:
                self.__sellProcess()
        '''
        
    def __buyIsSet(self, probability):
        return random.random() < probability