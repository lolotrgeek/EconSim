import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)

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