import asyncio
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)

import unittest
from source.Requests import Requests

class MockRequester():
    def __init__(self, response):
        self.response = response

    async def request(self, msg):
        return self.response

class RequestsTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.response = {"result": "success"}
        self.mock_requester = MockRequester(self.response)
        self.requests = Requests(self.mock_requester)

    async def test_make_request_success(self):
        topic = "test_topic"
        message = {"data": "test_data"}

        result = await self.requests.make_request(topic, message, None)
        self.assertEqual(result, self.response)

class RequestsStringTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.response = '{"result": "success"}'
        self.mock_requester = MockRequester(self.response)
        self.requests = Requests(self.mock_requester)

    async def test_make_request_string_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        result = await self.requests.make_request(topic, message, None)
        self.assertEqual(result, {"result": "success"})

class RequestsListTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.response = ["result1", "result2"]
        self.mock_requester = MockRequester(self.response)
        self.requests = Requests(self.mock_requester)
    async def test_make_request_list_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        result = await self.requests.make_request(topic, message, None)
        self.assertEqual(result, self.response)

class RequestsErrorTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.response = {"error": "request failed"}
        self.mock_requester = MockRequester(self.response)
        self.requests = Requests(self.mock_requester)
    async def test_make_request_error_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}

        with self.assertRaises(Exception) as context:
            result = await self.requests.make_request(topic, message, None)
            self.assertEqual(result, self.response)

class RequestsNoneTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_requester = MockRequester(None)
        self.requests = Requests(self.mock_requester)
    async def test_make_request_none_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}

        with self.assertRaises(Exception) as context:
            result = await self.requests.make_request(topic, message, None)
            self.assertEqual(result, '[Request Error] test_topic is None, None')

class RequestsNoDictTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.mock_requester = MockRequester(float(1))
        self.requests = Requests(self.mock_requester)

    async def test_make_request_no_dict_response(self):
        topic = "test_topic"
        message = {"data": "test_data"}
        with self.assertRaises(Exception) as context:
            result = await self.requests.make_request(topic, message, None)
            self.assertEqual(result, '[Request Error] test_topic got type float expected dict. 1')

class RequestsDictTests(unittest.IsolatedAsyncioTestCase):

    async def asyncSetUp(self):
        self.mock_requester = MockRequester({'open': 1, 'high': 2, 'low': 3, 'close': 4, 'volume': 5, 'timestamp': 6})
        self.requests = Requests(self.mock_requester)

    async def test_make_request_returns_dict(self):
        topic = 'candles'
        message = {'ticker': 'BTC', 'interval': '1h', 'limit': 10}
        result = await self.requests.make_request(topic, message, None)
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {'open': 1, 'high': 2, 'low': 3, 'close': 4, 'volume': 5, 'timestamp': 6})


if __name__ == '__main__':
    asyncio.run(unittest.main())