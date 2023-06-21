from flask import Flask, jsonify, request
from flask_socketio import SocketIO, emit
from time import sleep
from .Requests import Requests
import flask_monitoringdashboard as dashboard
import logging

def API(requester):
    app = Flask(__name__)
    logging.getLogger('werkzeug').disabled = True
    # dashboard.bind(app)
    requests = Requests(requester)
    @app.route('/')
    def index():
        return "hello"

    @app.route('/api/v1/sim_time', methods=['GET'])
    def get_sim_time():
        return jsonify({'sim_time': "TODO: req from clock process"})
    
    @app.route('/api/v1/get_agents', methods=['GET'])
    def get_agents():
        agents = requests.get_agents()
        if agents is None:
            return jsonify({'message': 'Agents not found.'}), 400
        return agents

    @app.route('/api/v1/candles', methods=['GET'])
    def candles():
        interval = request.args.get('interval')
        limit = request.args.get('limit', type=int)
        ticker = request.args.get('ticker')
        if (interval is None):
            interval = '15Min'
        if (limit is None):
            limit = 20
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return requests.get_price_bars(ticker, interval, limit)

    @app.route('/api/v1/create_asset', methods=['POST'])
    def create_asset():
        data = request.get_json()
        ticker = data['ticker']
        seed_price = data.get('seed_price', 100)
        seed_qty = data.get('seed_qty', 1000)
        seed_bid = data.get('seed_bid', 0.99)
        seed_ask = data.get('seed_ask', 1.01)
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return requests.create_asset(ticker, seed_price, seed_qty, seed_bid, seed_ask)

    @app.route('/api/v1/crypto/get_mempool', methods=['GET'])
    def get_mempool():
        limit = request.args.get('limit', type=int)
        if (limit is None):
            limit = 20
        return jsonify({'TODO': 'req from mempool process'})

    @app.route('/api/v1/get_order_book', methods=['GET'])
    def get_order_book():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return requests.get_order_book(ticker)

    @app.route('/api/v1/get_latest_trade', methods=['GET'])
    def get_latest_trade():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return requests.get_latest_trade(ticker)

    @app.route('/api/v1/get_trades', methods=['GET'])
    def get_trades():
        limit = request.args.get('limit', type=int)
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        if (limit is None):
            limit = 20
        return requests.get_trades(ticker, limit)

    @app.route('/api/v1/get_quotes', methods=['GET'])
    def get_quotes():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return requests.get_quotes(ticker)
        
    @app.route('/api/v1/get_best_bid', methods=['GET'])
    def get_best_bid():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return requests.get_best_bid(ticker)

    @app.route('/api/v1/get_best_ask', methods=['GET'])
    def get_best_ask():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return requests.get_best_ask(ticker)

    @app.route('/api/v1/get_midprice', methods=['GET'])
    def get_midprice():
        ticker = request.args.get('ticker')
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return jsonify({'midprice': requests.get_midprice(ticker)})

    @app.route('/api/v1/limit_buy', methods=['POST'])
    def limit_buy():
        data = request.get_json()
        ticker = data['ticker']
        price = data['price']
        qty = data['qty']
        creator = data['creator']
        fee = data['fee'], 0.0
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        if (price is None or price == ""):
            return jsonify({'message': 'Price not found.'}), 400
        if (qty is None or qty == ""):
            return jsonify({'message': 'Quantity not found.'}), 400
        if (creator is None or creator == ""):
            return jsonify({'message': 'Creator not found.'}), 400  
        return requests.limit_buy(ticker, price, qty, creator, fee)

    @app.route('/api/v1/limit_sell', methods=['POST'])
    def limit_sell():
        data = request.get_json()
        ticker = data['ticker']
        price = data['price']
        qty = data['qty']
        creator = data['creator']
        fee = data['fee'], 0.0
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        if (price is None or price == ""):
            return jsonify({'message': 'Price not found.'}), 400
        if (qty is None or qty == ""):
            return jsonify({'message': 'Quantity not found.'}), 400
        if (creator is None or creator == ""):
            return jsonify({'message': 'Creator not found.'}), 400        
        return requests.limit_sell(ticker, price, qty, creator, fee)

    @app.route('/api/v1/cancel_order', methods=['POST'])
    def cancel_order():
        data = request.get_json()
        order_id = data['id']
        if (order_id is None or order_id == ""):
            return jsonify({'message': 'Order ID not found.'}), 400
        return requests.cancel_order(order_id)

    @app.route('/api/v1/cancel_all_orders', methods=['POST'])
    def cancel_all_orders():
        data = request.get_json()
        agent = data['agent']
        ticker = data['ticker']
        if (ticker is None or ticker == "" or agent is None or agent == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        return requests.cancel_all_orders(ticker, agent)

    @app.route('/api/v1/market_buy', methods=['POST'])
    def market_buy():
        data = request.get_json()
        ticker = data['ticker']
        qty = data['qty']
        buyer = data['buyer']
        fee = data['fee'], 0.0
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        if (qty is None or qty == ""):
            return jsonify({'message': 'Quantity not found.'}), 400
        if (buyer is None or buyer == ""):
            return jsonify({'message': 'Creator not found.'}), 400          
        return requests.market_buy(ticker, qty, buyer, fee)

    @app.route('/api/v1/market_sell', methods=['POST'])
    def market_sell():
        data = request.get_json()
        ticker = data['ticker']
        qty = data['qty']
        seller = data['seller']
        fee = data['fee'], 0.0
        if (ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'}), 400
        if (qty is None or qty == ""):
            return jsonify({'message': 'Quantity not found.'}), 400
        if (seller is None or seller == ""):
            return jsonify({'message': 'Creator not found.'}), 400                
        return requests.market_sell(ticker, qty, seller, fee)

    return app

#TODO: for this to work we need to push data from the exchange and pull it to here then re-broadcast via websocket
def WebSockets(app, sim):
    socketio = SocketIO(app, cors_allowed_origins="*")

    @socketio.on('connect')
    def handle_connect():
        print('Client connected')
        # Send initial order book data to the client
        # emit('order_book', sim.exchange.get_order_book())


    @socketio.on('/ws/v1/get_order_book')
    def handle_get_order_book(data):
        ticker = data['ticker'] 
        if(ticker is None or ticker == ""):
            return jsonify({'message': 'Ticker not found.'})
        order_book = sim.exchange.get_order_book(ticker)
        if order_book:
            emit('order_book', jsonify({"bids": order_book.df['bids'].to_dict(), "asks": order_book.df['asks'].to_dict()}))
        else:
            emit('order_book', jsonify({'message': 'Order book not found.'}))
        sleep(1)

    return socketio