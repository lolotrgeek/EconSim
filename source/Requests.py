import json
import traceback
import asyncio

class Requests():
    """
    Creates an API for for making requests to the exchange process.
    """
    def __init__(self, requester):
        self.requester = requester
        self.timeout = 5
        self.max_tries = 1
        self.debug = True
        
    async def make_request(self, topic: str, message: dict, factory, tries=0):
        try:
            message['topic'] = topic
            msg = await self.requester.request(message)
            if msg is None:
                raise Exception(f'{topic} is None, {msg}')
            elif isinstance(msg, str):
                return json.loads(msg)
            elif isinstance(msg, list):
                return msg
            elif not isinstance(msg, dict):
                raise Exception(f'{topic} got type {type(msg)}, expected dict. Message: {msg}')
            elif 'error' in msg:
                raise Exception(f'{topic} error, {msg}')
            else:
                return msg
        except Exception as e:
            tries += 1
            if tries >= self.max_tries:
                error = {}
                error[topic] = f"[Request Error] {e}"
                if self.debug:
                    print("[Request Error]", e)
                    print(traceback.format_exc())
                return error
            await asyncio.sleep(0.1)
            return await self.make_request(topic, message, factory, tries)

