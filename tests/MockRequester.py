
class MockRequester():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self):
        self.responder = MockResponder()
        self.connected = False

    async def connect(self):
        self.connected = True
        pass
    
    async def request(self, msg):
        return msg

class MockResponder():
    """
    Mocked run_exchange and run_company callback responder
    """
    def __init__(self):
        self.test = "test"
        self.connected = False
                
    async def respond(self, callback):
        if self.test == 'test':
            self.test = False
            await callback({'topic': 'test'})
            return 'test'
        self.test = 'test'
        return 'STOP'
    
    async def lazy_respond(self, callback):
        if self.test == 'test':
            self.test = False
            await callback({'topic': 'test'})
            return 'test'
        self.test = 'test'
        return 'STOP'
    
    async def connect(self):
        self.connected = True
        pass

class MockPusher():
    """
    Mocked Pusher that connects directly to the MockSubscriber
    """
    def __init__(self):
        self.connected = False

    async def connect(self):
        self.connected = True
        pass
    
    async def push(self, msg):
        return msg