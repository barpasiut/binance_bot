import time
from binance.client import Client

class Orders:

    def __init__(self):
        self.__buyPrice = 0
        self.__currentOrderId = 0
        self.__makerBuyOrderTime = 0
        self.__makerSellOrderTime = 0
   
    def getBuyPrice(self):
        return self.__buyPrice
    
    def getBuyOrderTime(self):
        return self.__makerBuyOrderTime
    
    def getSellOrderTime(self):
        return self.__makerSellOrderTime
    
    def getCurrentOrderId(self):
        return self.__currentOrderId

    def makerBuy(self, cli, sym, qua, pri):
        print("self.__buyPrice:\n self.__buyPrice: {}\n".format(self.__buyPrice))
        self.__buyPrice = pri
        self.__currentOrderId = cli.order_limit_buy(symbol=sym, quantity=qua, price=pri)['orderId']
        print("self.__buyPrice2:\n self.__buyPrice: {}\n".format(self.__buyPrice))
        self.__makerBuyOrderTime = time.time()
        
    def makerSell(self, cli, sym, qua, pri):
        self.__currentOrderId = cli.order_limit_sell(symbol=sym, quantity=qua, price=pri)['orderId']
        self.__makerSellOrderTime = time.time()
