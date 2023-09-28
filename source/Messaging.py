import traceback
import json
import zmq
import zmq.asyncio
import asyncio
from .utils._utils import dumps
from decimal import Decimal
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

# logging.basicConfig(format="%(levelname)s: %(message)s", level=logging.WARN)

class DecimalEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, Decimal):
            return str(o)
        return super().default(o)

class Requester:
    def __init__(self, channel='5556', max_retries=3):
        self.channel = channel
        self.max_retries = max_retries
        self.request_timeout = 2500  # ms
        self.context = zmq.asyncio.Context()

    async def connect(self) -> None:
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f'tcp://127.0.0.1:{self.channel}')
        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.socket, zmq.POLLIN)

    async def request(self, msg) -> str:
        try:
            msg = json.dumps(msg, cls=DecimalEncoder)
            await self.socket.send_json(msg)
            response = await self.socket.recv_json()
            return json.loads(response)
        except zmq.ZMQError as e:
            print("[ZMQ Requester Error]", e, "Request:", msg)
            return {'error': repr(e)}
        except Exception as e:
            print("[Requester Error]", e, "Request:", msg)
            print(traceback.format_exc())
            return {'error': repr(e)}

    async def request_lazy(self, msg) -> str:
        try:
            await self.socket.send_json(msg)
            retries_left = self.max_retries
            while True:
                socks = dict(await self.poller.poll(self.request_timeout) )
                if socks.get(self.socket) == zmq.POLLIN:
                    reply = await self.socket.recv_json()
                    return reply
                else:
                    print("[Requester Warning] No response from server, retrying...")
                    retries_left -= 1
                    self.socket.setsockopt(zmq.LINGER, 0)
                    await self.socket.close()
                    if retries_left == 0:
                        return {'error': '[Requester Error] Maximum retries reached, no response from server.'}
                    
                    print("[Requester Warning] Reconnecting and resending request...")
                    self.socket = self.context.socket(zmq.REQ)
                    self.socket.connect(f'tcp://127.0.0.1:{self.channel}')
                    self.poller = zmq.asyncio.Poller()
                    self.poller.register(self.socket, zmq.POLLIN)
                    await self.socket.send_json(msg)
                    continue
        except zmq.ZMQError as e:
            print("[ZMQ Requester Error]", e, "Request:", msg)
            print(traceback.format_exc())
            return {'error': repr(e)}

        except Exception as e:
            print("[Requester Error]", e, "Request:", msg)
            print(traceback.format_exc())
            return {'error': repr(e)}

    async def close(self):
        await self.socket.close()
        await self.context.term()

class Responder:
    def __init__(self, channel='5556'):
        self.channel = channel
        self.listen_timeout = 500  # ms

    async def connect(self) -> None:
        self.context = zmq.asyncio.Context()
        self.socket = self.context.socket(zmq.REP)
        self.socket.bind(f'tcp://127.0.0.1:{self.channel}')
        self.poller = zmq.asyncio.Poller()
        self.poller.register(self.socket, zmq.POLLIN)        

    async def respond(self, callback=lambda msg: msg) -> str: 
        try:
            msg = await self.socket.recv_json()
            response = await callback(json.loads(msg))
            print(response)
            await self.socket.send_json(json.dumps(response, cls=DecimalEncoder))
            return response
        except zmq.ZMQError as e:
            print("[ZMQ Response Error]", e, "Request:", msg)
            print(traceback.format_exc())
            return json.dumps({'error': repr(e)})
        except Exception as e:
            print("[Response Error]", e, "Request:", msg)
            print(traceback.format_exc())
            await self.socket.send_json({'error': repr(e)})
            return json.dumps({'error': repr(e)})
        
    async def lazy_respond(self, callback=lambda msg: msg) -> str:
        try:
            socks = dict(await self.poller.poll(self.listen_timeout) )
            if socks.get(self.socket) == zmq.POLLIN:            
                msg = await self.socket.recv_json()
                response = await callback(msg)
                await self.socket.send_json(response)
                return response
        except zmq.ZMQError as e:
            print("[ZMQ Response Error]", e)
            print(traceback.format_exc())
            return json.dumps({'error': repr(e)})
        except Exception as e:
            print("[Response Error]", e)
            print(traceback.format_exc())
            await self.socket.send_json({'error': repr(e)})
            return json.dumps({'error': repr(e)})

class Broker:
    def __init__(self, request_side='5556', response_side='5557'):
        self.request_side = request_side
        self.response_side = response_side

    async def start(self) -> None:
        self.context = zmq.Context()
        self.requests_socket = self.context.socket(zmq.ROUTER)
        self.requests_socket.bind(f"tcp://127.0.0.1:{self.request_side}")
        self.responses_socket = self.context.socket(zmq.DEALER)
        self.responses_socket.bind(f"tcp://127.0.0.1:{self.response_side}")
        self.mon_socket = self.context.socket(zmq.PUB)
        self.mon_socket.bind("tcp://127.0.0.1:6969")

    async def route(self, cb=None) -> None:
        try:
            zmq.proxy(self.requests_socket, self.responses_socket, self.mon_socket)
        except Exception as e:
            print("[Broker Error]", e)

class Pusher():
    def __init__(self, channel='5558', bind=True):
        self.context = zmq.asyncio.Context()
        self.zmq_socket = self.context.socket(zmq.PUSH)
        self.address = f"tcp://127.0.0.1:{channel}"
        self.zmq_socket.setsockopt(zmq.CONFLATE, 1)
        self.zmq_socket.setsockopt(zmq.SNDHWM, 1)
        if bind:
            self.zmq_socket.bind(self.address)
        else:
            self.zmq_socket.connect(self.address)


    async def push(self, message) -> bool:
        try:
            await self.zmq_socket.send_json(message, zmq.NOBLOCK)
        except Exception as e:
            return {'error': repr(e)}

class Puller():
    def __init__(self, channel='5556', latest_only=True):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PULL)
        self.address = f"tcp://127.0.0.1:{channel}"
        if latest_only:
            self.socket.setsockopt(zmq.CONFLATE, 1)
        self.socket.connect(self.address)

    def pull(self) -> str:
        try:
            msg = self.socket.recv_json()
            return msg
        except Exception as e:
            print(e)
            return None
        
    def request(self, topic, args=None) -> str:
        return self.pull()

    def close(self) -> None:
        self.socket.close()
        self.context.term()

class Router():
    def __init__(self, producer='5558', consumer='5556'):
        self.context = zmq.Context()
        self.producer_socket = self.context.socket(zmq.PULL)
        self.producer_socket.bind(f"tcp://127.0.0.1:{producer}")
        self.consumer_socket = self.context.socket(zmq.PUSH)
        self.consumer_socket.bind(f"tcp://127.0.0.1:{consumer}")
        self.poller = zmq.Poller()
        self.poller.register(self.producer_socket, zmq.POLLIN)

    def route(self, cb=None) -> None:
        last_msg = {}
        while True:
            try:
                evts = dict(self.poller.poll(.5))
                if self.producer_socket in evts:
                    msg = self.producer_socket.recv_json(zmq.DONTWAIT)
                    if msg is not None and msg != last_msg and msg != {}:
                        last_msg = msg
                # print("last", last_msg)
                self.consumer_socket.send_json(last_msg)
            except Exception as e:
                print(e)
                continue  
    
class Publisher():
    def __init__(self, channel=5560):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.PUB)
        self.address = f"tcp://127.0.0.1:{channel}"
        self.socket.bind(self.address)

    def publish(self, topic, message) -> bool:
        try:
            payload = b"%s--> %s" % (topic.encode('utf-8'), message.encode('utf-8'))
            self.socket.send(payload)
            return True
        except Exception as e:
            print(e)
            return None
        
class Subscriber():
    def __init__(self, channel=5560, latest_only=True):
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.SUB)
        self.address = f"tcp://127.0.0.1:{channel}"
        self.socket.setsockopt_string(zmq.SUBSCRIBE, '')
        if latest_only:
            self.socket.setsockopt(zmq.CONFLATE, 1)
        self.socket.connect(self.address)

    def subscribe(self, topic) -> bool:
        try:
            self.socket.setsockopt_string(zmq.SUBSCRIBE, topic)
            raw_msg = self.socket.recv()
            msg = raw_msg.split(b"--> ")[1]
            return str(msg, 'utf-8')
        except Exception as e:
            print(e)
            return None