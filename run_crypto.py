from datetime import datetime
from source.crypto.CryptoCurrency import CryptoCurrency
from source.Messaging import Responder, Requester, Subscriber
import asyncio
from rich import print
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from source.utils._utils import dumps, string_to_time
from Channels import Channels

names= ['A', 'frXoX', 'wAt', 'Ayc', 'EXCAb', 'Qw', 'vbcY', 'ZM', 'j', 'nNLga', 'Ln', 'ao', 'k', 'icyJ', 'r', 'qk', 'BeHN', 'if', 'yAnL', 'sw']

def generate_cryptos(names, requester, time) -> dict:
    cryptos = {}
    for name in names:
        crypto = CryptoCurrency(name, time, requester)
        cryptos[crypto.symbol] = crypto
    return cryptos

async def run_crypto() -> None:
    #NOTE: the `fee` is the network fee and the exchange fee since the exchange fee is added to the transaction before it is added to the blockchain
    # while not how this works, this is makes calulating the overall fee easier for the simulator
    try:
        channels = Channels()
        responder = Responder(channels.crypto_channel)
        requester = Requester(channel=channels.exchange_channel)
        time_puller = Subscriber(channels.time_channel)
        asyncio.run(responder.connect())
        asyncio.run(requester.connect())

        def get_time():
            clock = time_puller.subscribe("time")
            if clock == None: 
                pass
            elif type(clock) is not str:
                pass
            else:
                return string_to_time(clock) 

        time = get_time()
        cryptos = generate_cryptos(names, requester, time)

        async def callback(msg):
            if 'asset' in msg:
                if msg['asset'] in cryptos:
                    if msg['topic'] == 'get_transactions': return dumps(await cryptos[msg['asset']].blockchain.get_transactions())
                    if msg['topic'] == 'get_transaction': return dumps(await cryptos[msg['asset']].blockchain.get_transaction(msg['id']))
                    elif msg['topic'] == 'add_transaction': return dumps(await cryptos[msg['asset']].blockchain.add_transaction(msg['asset'], msg['fee'], msg['amount'], msg['sender'], msg['recipient'], msg['dt']).to_dict())
                    elif msg['topic'] == 'get_mempool': return dumps(await cryptos[msg['asset']].blockchain.get_mempool())
                    elif msg['topic'] == 'get_pending_transactions': return dumps(await cryptos[msg['asset']].blockchain.mempool.get_pending_transactions(to_dicts=True))
                    elif msg['topic'] == 'get_confirmed_transactions': return dumps(await cryptos[msg['asset']].blockchain.mempool.get_confirmed_transactions(to_dicts=True))

                else: return f'unknown asset {msg["asset"]}'    
            else: return f'unknown topic {msg["topic"]}'

        while True:
            msg = await responder.respond(callback)
            if msg == None:
                continue

    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(run_crypto)
