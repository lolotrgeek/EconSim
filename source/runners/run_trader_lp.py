import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
sys.path.append(source_dir+'\\runners')
import traceback
from rich import print
import asyncio
from run_trader_defi import DefiTraderRunner
from source.exchange.DefiExchangeRequests import DefiExchangeRequests
from source.crypto.CryptoCurrencyRequests import CryptoCurrencyRequests
from source.agents.TradersDefi import RandomLiquidityProvider
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class DefiLiquidityProviderRunner(DefiTraderRunner):
    def __init__(self):
        super().__init__()

    async def pick_trader(self):
        self.trader = RandomLiquidityProvider('random_liquidity_provider', DefiExchangeRequests(self.exchange_requester), CryptoCurrencyRequests(self.requester))

    async def run(self) -> None:
        await super().run()

if __name__ == '__main__':
    try:
        runner = DefiLiquidityProviderRunner()
        asyncio.run(runner.run())
    except Exception as e:
        print("[Trader Error] ", e)
        traceback.print_exc()
        exit()