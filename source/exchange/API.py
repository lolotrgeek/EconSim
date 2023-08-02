from quart import Quart, websocket, jsonify, request
from .ExchangeRequests import ExchangeRequests as Requests

def API(requester):
    app = Quart(__name__)
    requests = Requests(requester)

    @app.route('/')
    async def index():
        return "hello"

    @app.route('/api/v1/sim_time', methods=['GET'])
    async def get_sim_time():
        return await requests.get_sim_time()
    
    @app.route('/api/v1/get_agents', methods=['GET'])
    async def get_agents():
        agents = requests.get_agents()
        if agents is None:
            return jsonify({'message': 'Agents not found.'}), 400
        return await agents

    @app.route('/api/v1/candles', methods=['GET'])
    async def candles():
        interval = request.args.get('interval')
        limit = request.args.get('limit', type=int)
        ticker = request.args.get('ticker')
        if (interval is None):
            interval = '15Min'
        if (limit is None):
            limit = 20
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return await requests.get_price_bars(ticker, interval, limit)

    @app.route('/api/v1/create_asset', methods=['POST'])
    async def create_asset():
        data = await request.get_json()
        ticker = data['ticker']
        seed_price = data.get('seed_price', 100)
        seed_qty = data.get('seed_qty', 1000)
        seed_bid = data.get('seed_bid', 0.99)
        seed_ask = data.get('seed_ask', 1.01)
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return await requests.create_asset(ticker, seed_price, seed_qty, seed_bid, seed_ask)

    @app.route('/api/v1/crypto/get_mempool', methods=['GET'])
    async def get_mempool():
        limit = request.args.get('limit', type=int)
        if (limit is None):
            limit = 20
        return jsonify({'TODO': 'req from mempool process'})

    @app.route('/api/v1/get_order_book', methods=['GET'])
    async def get_order_book():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return await requests.get_order_book(ticker)

    @app.route('/api/v1/get_latest_trade', methods=['GET'])
    async def get_latest_trade():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return await requests.get_latest_trade(ticker)

    @app.route('/api/v1/get_trades', methods=['GET'])
    async def get_trades():
        limit = request.args.get('limit', type=int)
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        if (limit is None):
            limit = 20
        return await requests.get_trades(ticker, limit)

    @app.route('/api/v1/get_quotes', methods=['GET'])
    async def get_quotes():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return await requests.get_quotes(ticker)
        
    @app.route('/api/v1/get_best_bid', methods=['GET'])
    async def get_best_bid():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return await requests.get_best_bid(ticker)

    @app.route('/api/v1/get_best_ask', methods=['GET'])
    async def get_best_ask():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return await requests.get_best_ask(ticker)

    @app.route('/api/v1/get_midprice', methods=['GET'])
    async def get_midprice():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return jsonify({'midprice': (await requests.get_midprice(ticker))})

    @app.route('/api/v1/limit_buy', methods=['POST'])
    async def limit_buy():
        data = await request.get_json()
        ticker = data['ticker']
        price = data['price']
        qty = data['qty']
        creator = data['creator']
        fee = data['fee'], 0.0
        if (ticker is None or ticker == ""):
            return await jsonify({'message': 'Ticker not found.'}), 400
        if (price is None or price == ""):
            return await jsonify({'message': 'Price not found.'}), 400
        if (qty is None or qty == ""):
            return await jsonify({'message': 'Quantity not found.'}), 400
        if (creator is None or creator == ""):
            return await jsonify({'message': 'Creator not found.'}), 400  
        return await requests.limit_buy(ticker, price, qty, creator, fee)

    @app.route('/api/v1/limit_sell', methods=['POST'])
    async def limit_sell():
        data = await request.get_json()
        ticker = data['ticker']
        price = data['price']
        qty = data['qty']
        creator = data['creator']
        fee = data['fee'], 0.0
        if (ticker is None or ticker == ""):
            return await jsonify({'message': 'Ticker not found.'}), 400
        if (price is None or price == ""):
            return await jsonify({'message': 'Price not found.'}), 400
        if (qty is None or qty == ""):
            return await jsonify({'message': 'Quantity not found.'}), 400
        if (creator is None or creator == ""):
            return await jsonify({'message': 'Creator not found.'}), 400        
        return await requests.limit_sell(ticker, price, qty, creator, fee)

    @app.route('/api/v1/cancel_order', methods=['POST'])
    async def cancel_order():
        data = await request.get_json()
        order_id = data['id']
        if (order_id is None or order_id == ""):
            return await jsonify({'message': 'Order ID not found.'}), 400
        return await requests.cancel_order(order_id)

    @app.route('/api/v1/cancel_all_orders', methods=['POST'])
    async def cancel_all_orders():
        data = await request.get_json()
        agent = data['agent']
        ticker = data['ticker']
        if (ticker is None or ticker == "" or agent is None or agent == ""):
            return await jsonify({'message': 'Ticker not found.'}), 400
        return await requests.cancel_all_orders(ticker, agent)

    @app.route('/api/v1/market_buy', methods=['POST'])
    async def market_buy():
        data = await request.get_json()
        ticker = data['ticker']
        qty = data['qty']
        buyer = data['buyer']
        fee = data['fee'], 0.0
        if (ticker is None or ticker == ""):
            return await jsonify({'message': 'Ticker not found.'}), 400
        if (qty is None or qty == ""):
            return await jsonify({'message': 'Quantity not found.'}), 400
        if (buyer is None or buyer == ""):
            return await jsonify({'message': 'Creator not found.'}), 400          
        return await requests.market_buy(ticker, qty, buyer, fee)

    @app.route('/api/v1/market_sell', methods=['POST'])
    async def market_sell():
        data = await request.get_json()
        ticker = data['ticker']
        qty = data['qty']
        seller = data['seller']
        fee = data['fee'], 0.0
        if (ticker is None or ticker == ""):
            return await jsonify({'message': 'Ticker not found.'}), 400
        if (qty is None or qty == ""):
            return await jsonify({'message': 'Quantity not found.'}), 400
        if (seller is None or seller == ""):
            return await jsonify({'message': 'Creator not found.'}), 400                
        return await requests.market_sell(ticker, qty, seller, fee)

    return app

#TODO: for this to work we need to push data from the exchange and pull it to here then re-broadcast via websocket
async def WebSockets(app, sim):
    pass