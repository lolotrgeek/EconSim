import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from httpx import AsyncClient
import pytest
from source.exchange.API import API
from .MockRequester import MockRequester

#CMD: pytest -v tests/test_API.py
requester = MockRequester()
app = API(requester=requester)    

@pytest.fixture
async def async_client():
    async with AsyncClient(app=app, base_url='http://test') as client:
        yield client

@pytest.mark.asyncio
async def test_index():
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')
    response = await async_client.get('/')
    assert response.status_code == 200, response.text == 'hello'

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, interval, limit, expected_status_code', [
    ('AAPL', '15Min', 20, 200),
    ('AAPL', None, 20, 200),
    ('AAPL', '15Min', None, 200),
    (None, None, None, 400),
    ('', '', '', 400)
])
async def test_candles( ticker, interval, limit, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')
    params = {'ticker': ticker, 'interval': interval, 'limit': limit}
    response = await async_client.get('/api/v1/candles', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, seed_price, seed_qty, seed_bid, seed_ask', [
    ('BTC', 100, 1000, 0.99, 1.01),
    ('ETH', None, None, None, None),
    (None, None, None, None, None)
])
@pytest.mark.asyncio
async def test_create_asset( ticker, seed_price, seed_qty, seed_bid, seed_ask):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    data = {'ticker': ticker, 'seed_price': seed_price, 'seed_qty': seed_qty, 'seed_bid': seed_bid, 'seed_ask': seed_ask}
    response = await async_client.post('/api/v1/create_asset', json=data)
    print(response)
    if ticker == None:
        assert response.status_code == 400
    else:
        assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.parametrize('limit, expected_status_code', [
    (20, 200)
])
async def test_get_mempool( limit, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    params = {'limit': limit}
    response = await async_client.get('/api/v1/crypto/get_mempool', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
async def test_get_order_book( ticker, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    params = {'ticker': ticker}
    response = await async_client.get('/api/v1/get_order_book', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
async def test_get_latest_trade( ticker, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    params = {'ticker': ticker}
    response = await async_client.get('/api/v1/get_latest_trade', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, limit, expected_status_code', [
    ('AAPL', 20, 200),
    ('', None, 400),
    (None, None, 400)
])
async def test_get_trades( ticker, limit, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    params = {'ticker': ticker, 'limit': limit}
    response = await async_client.get('/api/v1/get_trades', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
async def test_get_quotes( ticker, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    params = {'ticker': ticker}
    response = await async_client.get('/api/v1/get_quotes', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
async def test_get_best_bid( ticker, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    params = {'ticker': ticker}
    response = await async_client.get('/api/v1/get_best_bid', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
async def test_get_best_ask( ticker, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    params = {'ticker': ticker}
    response = await async_client.get('/api/v1/get_best_ask', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
async def test_get_midprice( ticker, expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    params = {'ticker': ticker}
    response = await async_client.get('/api/v1/get_midprice', params=params)
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, price, qty, creator, fee', [
    ('AAPL', 10.0, 5, 'user1', 0.1),
    ('async def', 20.0, 10, 'user2', 0.2)
])
async def test_limit_buy( ticker, price, qty, creator, fee):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    data = {
        'ticker': ticker,
        'price': price,
        'qty': qty,
        'creator': creator,
        'fee': fee
    }
    response = await async_client.post('/api/v1/limit_buy', json=data)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, price, qty, creator, fee', [
    ('AAPL', 10.0, 5, 'user1', 0.1),
    ('async def', 20.0, 10, 'user2', 0.2)
])
async def test_limit_sell( ticker, price, qty, creator, fee):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    data = {
        'ticker': ticker,
        'price': price,
        'qty': qty,
        'creator': creator,
        'fee': fee
    }
    response = await async_client.post('/api/v1/limit_sell', json=data)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.parametrize('order_id', [
    '12345',
    '67890'
])
async def test_cancel_order( order_id):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    data = {'id': order_id}
    response = await async_client.post('/api/v1/cancel_order', json=data)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.parametrize('agent, ticker', [
    ('agent1', 'AAPL'),
    ('agent2', 'async def')
])
async def test_cancel_all_orders( agent, ticker):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    data = {'agent': agent, 'ticker': ticker}
    response = await async_client.post('/api/v1/cancel_all_orders', json=data)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, qty, buyer, fee', [
    ('AAPL', 10, 'buyer1', 0.1),
    ('async def', 20, 'buyer2', 0.2)
])
async def test_market_buy( ticker, qty, buyer, fee):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    data = {'ticker': ticker, 'qty': qty, 'buyer': buyer, 'fee': fee}
    response = await async_client.post('/api/v1/market_buy', json=data)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.parametrize('ticker, qty, seller, fee', [
    ('AAPL', 10, 'seller1', 0.1),
    ('async def', 20, 'seller2', 0.2)
])
async def test_market_sell( ticker, qty, seller, fee):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    data = {'ticker': ticker, 'qty': qty, 'seller': seller, 'fee': fee}
    response = await async_client.post('/api/v1/market_sell', json=data)
    assert response.status_code == 200

@pytest.mark.asyncio
@pytest.mark.parametrize('expected_status_code', [
    200
])
async def test_get_agents( expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    response = await async_client.get('/api/v1/get_agents')
    assert response.status_code == expected_status_code

@pytest.mark.asyncio
@pytest.mark.parametrize('expected_status_code', [
    200
])
async def test_get_positions( expected_status_code):
    await requester.init()
    async_client = AsyncClient(app=app, base_url='http://test')    
    response = await async_client.get('/api/v1/get_positions')
    assert response.status_code == expected_status_code

if __name__ == '__main__':
    pytest.main()