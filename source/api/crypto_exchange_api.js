import express from 'express'
import Requester from './Requester.js'
const app = express()


app.get('/', (req, res) => {
    res.send('This is the exchange api.')
})

const sim_time_requests = new Requester('5571')
app.get('/api/v1/sim_time', async (req, res) => {
    await sim_time_requests.request('sim_time', {})
    res.json(sim_time_requests.latest_result)
})

const get_tickers_requests = new Requester('5571')
app.get('/api/v1/get_tickers', async (req, res) => {
    await get_tickers_requests.request('get_tickers', {})
    res.json(get_tickers_requests.latest_result)
})

const get_agents_requests = new Requester('5571')
app.get('/api/v1/get_agents', async (req, res) => {
    await get_agents_requests.request('get_agents_simple', {})
    const agents = get_agents_requests.latest_result
    if (agents === null) {
        res.status(400).json({ message: 'Agents not found.' })
    } else {
        res.json(agents)
    }
})

const get_positions_requests = {}
app.get('/api/v1/get_positions', async (req, res) => {
    const agent = req.query.agent
    const page_size = parseInt(req.query.page_size) || 10
    const page = parseInt(req.query.page) || 1

    if (!get_positions_requests[agent]) get_positions_requests[agent] = new Requester('5571')
    if (!agent) { res.status(400).json({ message: 'Agent not found.' }); return }

    await get_positions_requests[agent].request('get_positions', {
        agent: agent,
        page_size: page_size,
        page: page,
    })
    res.json(get_positions_requests[agent].latest_result)
})

const get_candles_requests = {}
app.get('/api/v1/candles', async (req, res) => {
    const ticker = req.query.ticker
    const interval = req.query.interval || '15T'
    const limit = parseInt(req.query.limit) || 20
    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    if (!get_candles_requests[ticker]) get_candles_requests[ticker] = new Requester('5571')

    await get_candles_requests[ticker].request('candles', {
        ticker: ticker,
        interval: interval,
        limit: limit,
    })

    res.json(get_candles_requests[ticker].latest_result)
})

const order_book_requesters = {}
app.get('/api/v1/get_order_book', async (req, res) => {
    const ticker = req.query.ticker
    const limit = parseInt(req.query.limit) || 20

    if (!order_book_requesters[ticker]) order_book_requesters[ticker] = new Requester('5571')

    if (!ticker) { res.status(400).json({ message: 'Ticker not found.' }); return }

    await order_book_requesters[ticker].request('order_book', { ticker: ticker, limit: limit, })
    res.json(order_book_requesters[ticker].latest_result)
})

const get_latest_trade_requesters = {}
app.get('/api/v1/get_latest_trade', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) { res.status(400).json({ message: 'Ticker not found.' }); return}
    if (!get_latest_trade_requesters[ticker]) get_latest_trade_requesters[ticker] = new Requester('5571')

    await get_latest_trade_requests[ticker].request('latest_trade', {
        ticker: ticker,
    })

    res.json(get_latest_trade_requests[ticker].latest_result)
})

const get_trades_requests = {}
app.get('/api/v1/get_trades', async (req, res) => {
    const ticker = req.query.ticker
    const limit = parseInt(req.query.limit) || 20

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }
    
    if (!get_trades_requests[ticker]) get_trades_requests[ticker] = new Requester('5571')

    await get_trades_requests[ticker].request('trades', {
        ticker: ticker,
        limit: limit,
    })

    res.json(get_trades_requests[ticker].latest_result)
})

const get_quotes_requests = {}
app.get('/api/v1/get_quotes', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    if (!get_quotes_requests[ticker]) get_quotes_requests[ticker] = new Requester('5571')

    await get_quotes_requests[ticker].request('quotes', {
        ticker: ticker,
    })

    res.json(get_quotes_requests[ticker].latest_result)
})

const get_best_bid_requests = {}
app.get('/api/v1/get_best_bid', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    if (!get_best_bid_requests[ticker]) get_best_bid_requests[ticker] = new Requester('5571')

    await get_best_bid_requests[ticker].request('best_bid', {
        ticker: ticker,
    })

    res.json(get_best_bid_requests[ticker].latest_result)
})

const get_best_ask_requests = {}
app.get('/api/v1/get_best_ask', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    if (!get_best_ask_requests[ticker]) get_best_ask_requests[ticker] = new Requester('5571')

    await get_best_ask_requests[ticker].request('best_ask', {
        ticker: ticker,
    })

    res.json(get_best_ask_requests[ticker].latest_result)
})

const get_midprice_requests = {}
app.get('/api/v1/get_midprice', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    if (!get_midprice_requests[ticker]) get_midprice_requests[ticker] = new Requester('5571')

    await get_midprice_requests[ticker].request('midprice', {
        ticker: ticker,
    })

    res.json({ midprice: get_midprice_requests[ticker].latest_result })
})

const limit_buy_requests = {}
app.post('/api/v1/limit_buy', async (req, res) => {
    const data = req.body
    const ticker = data.ticker
    const price = data.price
    const qty = data.qty
    const creator = data.creator
    const fee = data.fee || 0.0

    if (!ticker || !price || !qty || !creator) {
        res.status(400).json({ message: 'Invalid data. Check required fields.' })
        return
    }

    if (!limit_buy_requests[creator]) limit_buy_requests[creator] = new Requester('5571')

    await limit_buy_requests[creator].request('limit_buy', {
        ticker: ticker,
        price: price,
        qty: qty,
        creator: creator,
        fee: fee,
    })

    res.json(limit_buy_requests[creator].latest_result)
})

const limit_sell_requests = {}
app.post('/api/v1/limit_sell', async (req, res) => {
    const data = req.body
    const ticker = data.ticker
    const price = data.price
    const qty = data.qty
    const creator = data.creator
    const fee = data.fee || 0.0

    if (!ticker || !price || !qty || !creator) {
        res.status(400).json({ message: 'Invalid data. Check required fields.' })
        return
    }

    if (!limit_sell_requests[creator]) limit_sell_requests[creator] = new Requester('5571')

    await limit_sell_requests[creator].request('limit_sell', {
        ticker: ticker,
        price: price,
        qty: qty,
        creator: creator,
        fee: fee,
    })

    res.json(limit_sell_requests[creator].latest_result)
})

const cancel_order_requests = {}
app.post('/api/v1/cancel_order', async (req, res) => {
    const data = req.body
    const order_id = data.id
    const creator = data.creator

    if (!order_id || !creator) {
        res.status(400).json({ message: 'Invalid data. Check required fields.' })
        return
    }

    if(!cancel_order_requests[creator]) cancel_order_requests[creator] = new Requester('5571')

    await cancel_order_requests[creator].request('cancel_order', {
        order_id: order_id,
    })

    res.json(cancel_order_requests[creator].latest_result)
})

const cancel_all_orders_requests = {}
app.post('/api/v1/cancel_all_orders', async (req, res) => {
    const data = req.body
    const agent = data.agent
    const ticker = data.ticker

    if (!ticker || !agent) {
        res.status(400).json({ message: 'Invalid data. Check required fields.' })
        return
    }

    if(!cancel_order_requests[agent]) cancel_order_requests[agent] = new Requester('5571')


    await cancel_all_orders_requests[agent].request('cancel_all_orders', {
        ticker: ticker,
        agent: agent,
    })

    res.json(cancel_all_orders_requests[agent].latest_result)
})

const market_buy_requests = {}
app.post('/api/v1/market_buy', async (req, res) => {
    const data = req.body
    const ticker = data.ticker
    const qty = data.qty
    const buyer = data.buyer
    const fee = data.fee || 0.0

    if (!ticker || !qty || !buyer) {
        res.status(400).json({ message: 'Invalid data. Check required fields.' })
        return
    }

    if (!market_buy_requests[creator]) market_buy_requests[creator] = new Requester('5571')

    await market_buy_requests[creator].request('market_buy', {
        ticker: ticker,
        qty: qty,
        buyer: buyer,
        fee: fee,
    })

    res.json(market_buy_requests[creator].latest_result)
})

const market_sell_requests = {}
app.post('/api/v1/market_sell', async (req, res) => {
    const data = req.body
    const ticker = data.ticker
    const qty = data.qty
    const seller = data.seller
    const fee = data.fee || 0.0

    if (!ticker || !qty || !seller) {
        res.status(400).json({ message: 'Invalid data. Check required fields.' })
        return
    }

    if (!market_sell_requests[creator]) market_sell_requests[creator] = new Requester('5571')

    await market_sell_requests[creator].request('market_sell', {
        ticker: ticker,
        qty: qty,
        seller: seller,
        fee: fee,
    })

    res.json(market_sell_requests[creator].latest_result)
})

app.listen(5000, () => {
    console.log('Exchange API started on http://localhost:5000')
})
