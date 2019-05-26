class FiltersType:
    
    PRICE_FILTER = 0
    PERCENT_PRICE = 1
    LOT_SIZE = 2
    MIN_NOTIONAL = 3
    ICEBERG_PARTS = 4
    MAX_NUM_ALGO_ORDERS = 5

class Filters:
    
    def __init__(self, client, symbol):
        self.__client = client
        self.__filters = []
        self.__updateFilters(symbol)
    
    def __updateFilters(self, symbol):
        self.__filters = self.__client.get_symbol_info(symbol)["filters"]

    def getFilters(self):
        return self.__filters
