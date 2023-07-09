import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
import pytest
from flask import Flask
from flask import jsonify, request
from source.API import API
from .MockRequester import MockRequester

#CMD: pytest -v tests/test_API.py

@pytest.fixture
def client():
    app = API(MockRequester())
    with app.test_client() as client:
        yield client


def test_index(client):
    response = client.get('/')
    assert response.status_code == 200
    assert response.get_data(as_text=True) == 'hello'

@pytest.mark.parametrize('ticker, interval, limit, expected_status_code', [
    ('AAPL', '15Min', 20, 200),
    ('AAPL', None, 20, 200),
    ('AAPL', '15Min', None, 200),
    (None, None, None, 400),
    ('', '', '', 400)
])
def test_candles(client, ticker, interval, limit, expected_status_code):
    params = {'ticker': ticker, 'interval': interval, 'limit': limit}
    response = client.get('/api/v1/candles', query_string=params)
    assert response.status_code == expected_status_code

@pytest.mark.parametrize('ticker, seed_price, seed_qty, seed_bid, seed_ask', [
    ('BTC', 100, 1000, 0.99, 1.01),
    ('ETH', None, None, None, None),
    (None, None, None, None, None)
])
def test_create_asset(client, ticker, seed_price, seed_qty, seed_bid, seed_ask):
    data = {'ticker': ticker, 'seed_price': seed_price, 'seed_qty': seed_qty, 'seed_bid': seed_bid, 'seed_ask': seed_ask}
    response = client.post('/api/v1/create_asset', json=data)
    print(response)
    if ticker == None:
        assert response.status_code == 400
    else:
        assert response.status_code == 200

@pytest.mark.parametrize('limit, expected_status_code', [
    (20, 200)
])
def test_get_mempool(client, limit, expected_status_code):
    params = {'limit': limit}
    response = client.get('/api/v1/crypto/get_mempool', query_string=params)
    assert response.status_code == expected_status_code

@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
def test_get_order_book(client, ticker, expected_status_code):
    params = {'ticker': ticker}
    response = client.get('/api/v1/get_order_book', query_string=params)
    assert response.status_code == expected_status_code

@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
def test_get_latest_trade(client, ticker, expected_status_code):
    params = {'ticker': ticker}
    response = client.get('/api/v1/get_latest_trade', query_string=params)
    assert response.status_code == expected_status_code

@pytest.mark.parametrize('ticker, limit, expected_status_code', [
    ('AAPL', 20, 200),
    ('', None, 400),
    (None, None, 400)
])
def test_get_trades(client, ticker, limit, expected_status_code):
    params = {'ticker': ticker, 'limit': limit}
    response = client.get('/api/v1/get_trades', query_string=params)
    assert response.status_code == expected_status_code


@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
def test_get_quotes(client, ticker, expected_status_code):
    params = {'ticker': ticker}
    response = client.get('/api/v1/get_quotes', query_string=params)
    assert response.status_code == expected_status_code


@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
def test_get_best_bid(client, ticker, expected_status_code):
    params = {'ticker': ticker}
    response = client.get('/api/v1/get_best_bid', query_string=params)
    assert response.status_code == expected_status_code


@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
def test_get_best_ask(client, ticker, expected_status_code):
    params = {'ticker': ticker}
    response = client.get('/api/v1/get_best_ask', query_string=params)
    assert response.status_code == expected_status_code


@pytest.mark.parametrize('ticker, expected_status_code', [
    ('AAPL', 200),
    (None, 400),
    ('', 400)
])
def test_get_midprice(client, ticker, expected_status_code):
    params = {'ticker': ticker}
    response = client.get('/api/v1/get_midprice', query_string=params)
    assert response.status_code == expected_status_code


@pytest.mark.parametrize('ticker, price, qty, creator, fee', [
    ('AAPL', 10.0, 5, 'user1', 0.1),
    ('DEF', 20.0, 10, 'user2', 0.2)
])
def test_limit_buy(client, ticker, price, qty, creator, fee):
    data = {
        'ticker': ticker,
        'price': price,
        'qty': qty,
        'creator': creator,
        'fee': fee
    }
    response = client.post('/api/v1/limit_buy', json=data)
    assert response.status_code == 200


@pytest.mark.parametrize('ticker, price, qty, creator, fee', [
    ('AAPL', 10.0, 5, 'user1', 0.1),
    ('DEF', 20.0, 10, 'user2', 0.2)
])
def test_limit_sell(client, ticker, price, qty, creator, fee):
    data = {
        'ticker': ticker,
        'price': price,
        'qty': qty,
        'creator': creator,
        'fee': fee
    }
    response = client.post('/api/v1/limit_sell', json=data)
    assert response.status_code == 200


@pytest.mark.parametrize('order_id', [
    '12345',
    '67890'
])
def test_cancel_order(client, order_id):
    data = {'id': order_id}
    response = client.post('/api/v1/cancel_order', json=data)
    assert response.status_code == 200


@pytest.mark.parametrize('agent, ticker', [
    ('agent1', 'AAPL'),
    ('agent2', 'DEF')
])
def test_cancel_all_orders(client, agent, ticker):
    data = {'agent': agent, 'ticker': ticker}
    response = client.post('/api/v1/cancel_all_orders', json=data)
    assert response.status_code == 200


@pytest.mark.parametrize('ticker, qty, buyer, fee', [
    ('AAPL', 10, 'buyer1', 0.1),
    ('DEF', 20, 'buyer2', 0.2)
])
def test_market_buy(client, ticker, qty, buyer, fee):
    data = {'ticker': ticker, 'qty': qty, 'buyer': buyer, 'fee': fee}
    response = client.post('/api/v1/market_buy', json=data)
    assert response.status_code == 200


@pytest.mark.parametrize('ticker, qty, seller, fee', [
    ('AAPL', 10, 'seller1', 0.1),
    ('DEF', 20, 'seller2', 0.2)
])
def test_market_sell(client, ticker, qty, seller, fee):
    data = {'ticker': ticker, 'qty': qty, 'seller': seller, 'fee': fee}
    response = client.post('/api/v1/market_sell', json=data)
    assert response.status_code == 200

# Test get_agents endpoint
@pytest.mark.parametrize('expected_status_code', [
    200
])
def test_get_agents(client, expected_status_code):
    response = client.get('/api/v1/get_agents')
    assert response.status_code == expected_status_code

if __name__ == '__main__':
    pytest.main()