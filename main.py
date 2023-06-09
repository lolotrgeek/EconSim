from source.backend.OrderSide import OrderSide
from source.backend.LimitOrder import LimitOrder
from source.backend.OrderBook import OrderBook
from source.backend.Exchange import Exchange
from source.backend.AgentRemote import AgentRemote
from source.backend.Agents import RandomMarketTaker, NaiveMarketMaker, CryptoMarketMaker, CryptoMarketTaker, RemoteTrader
from source.backend.helpers import plot_bars
from source.backend.run import main
import sys

if __name__ == '__main__':
    try:
        main()        
        print('done...')
        exit(0)
    except:
        print(sys.exc_info()[0])
        exit(0)
        

# export all imports
__all__ = [
    'OrderSide',
    'LimitOrder',
    'OrderBook',
    'Exchange',
    'AgentRemote',
    'RandomMarketTaker',
    'NaiveMarketMaker',
    'CryptoMarketMaker',
    'CryptoMarketTaker',
    'RemoteTrader',
    'plot_bars',
]