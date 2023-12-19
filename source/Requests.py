import time
import json
import traceback
import asyncio

class Requests():
    """
    Creates an Interface for making requests.
    """
    def __init__(self, requester, cache=False):
        self.requester = requester
        self.cache=cache
        self.timeout = 5
        self.max_tries = 1
        self.debug = True
        self.message_cache = {}
        self.cache_duration = 5  # Cache duration in seconds (adjust as needed)

    async def make_request(self, topic: str, message: dict, factory, tries=0) -> str:
        try:
            # Check if the message is already cached and not expired
            if self.cache and topic in self.message_cache:
                cached_msg, expiration_time = self.message_cache[topic]
                current_time = time.time()
                if current_time < expiration_time:
                    return cached_msg

            message['topic'] = topic
            msg = await self.requester.request(message)

            if msg is None:
                raise Exception(f'{topic} is None, {msg}')
            elif isinstance(msg, str):
                parsed_msg = json.loads(msg) 
            elif isinstance(msg, list):
                parsed_msg = msg
            elif not isinstance(msg, dict):
                raise Exception(f'{topic} got type {type(msg)}, expected dict. Message: {msg}')
            elif 'error' in msg:
                raise Exception(f'{topic} error, {msg}')
            elif 'warning' in msg:
                if self.debug: print(f'{topic}warning {msg}')
            else:
                parsed_msg = msg

            # Cache the message along with the expiration time
            expiration_time = time.time() + self.cache_duration
            self.message_cache[topic] = (parsed_msg, expiration_time)

            return parsed_msg
        except Exception as e:
            tries += 1
            if tries >= self.max_tries:
                error = {}
                error[topic] = f"[Request Error] {e}"
                if self.debug:
                    print("[Request Error]", e, topic, message)
                    print(traceback.format_exc())
                return json.dumps(error)
            await asyncio.sleep(0.1)
            return await self.make_request(topic, message, factory, tries)
