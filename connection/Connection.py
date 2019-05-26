from binance.client import Client
from connection.Keys import Keys
from connection.Streams import Streams
from connection.Orders import Orders

class Connection:

    def __init__(self):
        self.client = Client(Keys.API_PUBLIC_KEY, Keys.API_PRIVATE_KEY)
        self.streams = Streams(self.client)
        self.orders = Orders()
        