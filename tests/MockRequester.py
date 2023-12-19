
class MockRequester():
    """
    Mocked Requester that connects directly to the MockResponder
    """
    def __init__(self):
        self.responder = MockResponder()

    async def init(self):
        await self.responder.init()
    
    async def request(self, msg):
        return await self.responder.callback(msg)

class MockResponder():
    """
    Mocked run_exchange and run_company callback responder
    """
    def __init__(self):
        super().__init__()
                
    async def respond(self, msg):
        return await self.callback(msg)
    
    async def connect(self):
        pass