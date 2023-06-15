from source.types.OrderSide import OrderSide
from source.types.LimitOrder import LimitOrder
from source.types.OrderBook import OrderBook
from source.Exchange import Exchange
from source.Agents import RandomMarketTaker, NaiveMarketMaker, CryptoMarketMaker, CryptoMarketTaker
from source.run import main
import sys
import traceback

if __name__ == '__main__':
    try:
        main()        
        print('done...')
        exit(0)
    except:
        # print(sys.exc_info()[2])
        # print(traceback.format_exc())
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
]