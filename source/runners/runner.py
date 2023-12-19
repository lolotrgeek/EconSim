from source.Channels import Channels
from source.Messaging import Subscriber
from source.utils._utils import string_to_time

class Runner():
    def __init__(self):
        self.channels = Channels()
        self.time_puller = Subscriber(self.channels.time_channel)

    async def get_time(self):
        clock = self.time_puller.subscribe("time")
        if clock == None: 
            pass
        elif type(clock) is not str:
            pass
        else: 
            return string_to_time(clock)