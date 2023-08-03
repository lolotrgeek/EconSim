from datetime import datetime
from source.crypto.Blockchain import Blockchain
from source.Messaging import Responder
import asyncio
from rich import print
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
from source.utils._utils import dumps


async def run_crypto(crypto_channel = 5571) -> None:
    #NOTE: the `fee` is the network fee and the exchange fee since the exchange fee is added to the transaction before it is added to the blockchain
    # while not how this works, this is makes calulating the overall fee easier for the simulator
    try:
        responder = Responder(crypto_channel)
        asyncio.run(responder.connect())
        blockchain = Blockchain()

        async def callback(msg):
            if msg['topic'] == 'get_transactions': return dumps(await blockchain.get_transactions())
            elif msg['topic'] == 'add_transaction': return dumps(await blockchain.add_transaction(msg['ticker'], msg['fee'], msg['amount'], msg['sender'], msg['recipient'], msg['dt']))
            else: return f'unknown topic {msg["topic"]}'

        while True:
            msg = await responder.respond(callback)
            if msg == None:
                continue

    except Exception as e:
        print(e)

if __name__ == '__main__':
    asyncio.run(run_crypto)
