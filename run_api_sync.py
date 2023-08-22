import zmq
import traceback
from flask import Flask, request, jsonify
import json
import time

class Requester:
    def __init__(self, channel='5570'):
        self.channel = channel
        self.context = zmq.Context()
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(f'tcp://127.0.0.1:{self.channel}')
        self.poller = zmq.Poller()
        self.poller.register(self.socket, zmq.POLLIN)        

    def request(self, topic, msg) -> str:
        try:
            time.sleep(0.1)
            msg['topic'] = topic
            self.socket.send_json(msg)
            return self.socket.recv_json()
        except zmq.ZMQError as e:
            print("[ZMQ Requester Error]", e, "Request:", msg)
            return json.dumps({"topic": topic, "error": e.strerror})
        except Exception as e:
            print("[Requester Error]", e, "Request:", msg)
            print(traceback.format_exc())
            return json.dumps({"topic": topic, "error": str(e)})

app = Flask(__name__)

@app.route('/')
def index():
    return "hello"

@app.route('/api/v1/sim_time', methods=['GET'])
def get_sim_time(requests = Requester()) -> str:
    return requests.request('sim_time', {})

@app.route('/api/v1/get_agents', methods=['GET'])
def get_agents(requests = Requester()) -> str:
    agents = requests.request('get_agents_simple', {})
    if agents is None:
        return jsonify({'message': 'Agents not found.'}), 400
    return agents

@app.route('/api/v1/get_positions', methods=['GET'])
def get_positions(requests = Requester()) -> str:
    agent = request.args.get('agent')
    page_size = request.args.get('page_size', type=int)
    page = request.args.get('page', type=int)
    if (agent is None or agent == ""):
        return jsonify({'message': 'Agent not found.'}), 400
    if (page_size is None or page_size == ""):
        page_size = 10
    if (page is None or page == ""):
        page = 1
    return requests.request('get_positions', {'agent': agent, 'page_size': page_size, "page": page})

@app.route('/api/v1/candles', methods=['GET'])
def candles(requests = Requester()) -> str:
    interval = request.args.get('interval')
    limit = request.args.get('limit', type=int)
    ticker = request.args.get('ticker')
    if (interval is None):
        interval = '15T'
    if (limit is None):
        limit = 20
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    return requests.request('candles', {'ticker': ticker, 'interval': interval, 'limit': limit})

@app.route('/api/v1/create_asset', methods=['POST'])
def create_asset(requests = Requester()) -> str:
    data = request.get_json()
    ticker = data['ticker']
    seed_price = data.get('seed_price', 100)
    seed_qty = data.get('seed_qty', 1000)
    seed_bid = data.get('seed_bid', 0.99)
    seed_ask = data.get('seed_ask', 1.01)
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    return requests.request('create_asset', {'ticker': ticker, 'qty': seed_qty,'seed_price': seed_price, 'seed_bid': seed_bid, 'seed_ask': seed_ask})

@app.route('/api/v1/get_order_book', methods=['GET'])
def get_order_book(requests = Requester()) -> str:
    ticker = request.args.get('ticker')
    limit = request.args.get('limit', type=int)
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    if (limit is None or limit == ""):
        limit = 20
    return requests.request('order_book', {'ticker': ticker, 'limit': limit})

@app.route('/api/v1/get_latest_trade', methods=['GET'])
def get_latest_trade(requests = Requester()) -> str:
    ticker = request.args.get('ticker')
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    return requests.request('latest_trade', {'ticker': ticker})

@app.route('/api/v1/get_trades', methods=['GET'])
def get_trades(requests = Requester()) -> str:
    limit = request.args.get('limit', type=int)
    ticker = request.args.get('ticker')
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    if (limit is None):
        limit = 20
    return requests.request('trades', {'ticker': ticker, 'limit': limit})

@app.route('/api/v1/get_quotes', methods=['GET'])
def get_quotes(requests = Requester()) -> str:
    ticker = request.args.get('ticker')
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    return requests.request('quotes', {'ticker': ticker})
    
@app.route('/api/v1/get_best_bid', methods=['GET'])
def get_best_bid(requests = Requester()) -> str:
    ticker = request.args.get('ticker')
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    return requests.request('best_bid', {'ticker': ticker})

@app.route('/api/v1/get_best_ask', methods=['GET'])
def get_best_ask(requests = Requester()) -> str:
    ticker = request.args.get('ticker')
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    return requests.request('best_ask', {'ticker': ticker})

@app.route('/api/v1/get_midprice', methods=['GET'])
def get_midprice(requests = Requester()) -> str:
    ticker = request.args.get('ticker')
    if (ticker is None or ticker == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    return jsonify({'midprice': (requests.request('midprice', {'ticker': ticker}))})

@app.route('/api/v1/limit_buy', methods=['POST'])
def limit_buy(requests = Requester()) -> str:
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
    return requests.request('limit_buy', {'ticker': ticker, 'price': price, 'qty': qty, 'creator': creator, 'fee': fee})

@app.route('/api/v1/limit_sell', methods=['POST'])
def limit_sell(requests = Requester()) -> str:
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
    return requests.request('limit_sell', {'ticker': ticker, 'price': price, 'qty': qty, 'creator': creator, 'fee': fee})

@app.route('/api/v1/cancel_order', methods=['POST'])
def cancel_order(requests = Requester()) -> str:
    data = request.get_json()
    order_id = data['id']
    if (order_id is None or order_id == ""):
        return jsonify({'message': 'Order ID not found.'}), 400
    return requests.request('cancel_order', {'order_id': order_id})

@app.route('/api/v1/cancel_all_orders', methods=['POST'])
def cancel_all_orders(requests = Requester()) -> str:
    data = request.get_json()
    agent = data['agent']
    ticker = data['ticker']
    if (ticker is None or ticker == "" or agent is None or agent == ""):
        return jsonify({'message': 'Ticker not found.'}), 400
    return requests.request('cancel_all_orders', {'ticker': ticker, 'agent': agent})

@app.route('/api/v1/market_buy', methods=['POST'])
def market_buy(requests = Requester()) -> str:
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
    return requests.request('market_buy', {'ticker': ticker, 'qty': qty, 'buyer': buyer, 'fee': fee})

@app.route('/api/v1/market_sell', methods=['POST'])
def market_sell(requests = Requester()) -> str:
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
    return requests.request('market_sell', {'ticker': ticker, 'qty': qty, 'seller': seller, 'fee': fee})
