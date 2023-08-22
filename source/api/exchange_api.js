import express from 'express'
import Requester from './Requester.js'
const app = express()


app.get('/', (req, res) => {
    res.send('This is the exchange api.')
})

const sim_time_requests = new Requester('5570')
app.get('/api/v1/sim_time', async (req, res) => {
    await sim_time_requests.request('sim_time', {})
    res.json(sim_time_requests.latest_result)
})

const get_tickers_requests = new Requester('5570')
app.get('/api/v1/get_tickers', async (req, res) => {
    await get_tickers_requests.request('get_tickers', {})
    res.json(get_tickers_requests.latest_result)
})


const get_agents_requests = new Requester('5570')
app.get('/api/v1/get_agents', async (req, res) => {
    await get_agents_requests.request('get_agents_simple', {})
    const agents = get_agents_requests.latest_result
    if (agents === null) {
        res.status(400).json({ message: 'Agents not found.' })
    } else {
        res.json(agents)
    }
})

const get_positions_requests = new Requester('5570')
app.get('/api/v1/get_positions', async (req, res) => {
    const agent = req.query.agent
    const page_size = parseInt(req.query.page_size) || 10
    const page = parseInt(req.query.page) || 1

    if (!agent) {
        res.status(400).json({ message: 'Agent not found.' })
        return
    }

    await get_positions_requests.request('get_positions', {
        agent: agent,
        page_size: page_size,
        page: page,
    })
    res.json(get_positions_requests.latest_result)
})

const get_candles_requests = new Requester('5570')
app.get('/api/v1/candles', async (req, res) => {
    const ticker = req.query.ticker
    const interval = req.query.interval || '15T'
    const limit = parseInt(req.query.limit) || 20
    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }
    await get_candles_requests.request('candles', {
        ticker: ticker,
        interval: interval,
        limit: limit,
    })

    res.json(get_candles_requests.latest_result)
})

const create_assets_requests = new Requester('5570')
app.post('/api/v1/create_asset', async (req, res) => {
    const data = req.body
    const ticker = data.ticker
    const seed_price = data.seed_price || 100
    const seed_qty = data.seed_qty || 1000
    const seed_bid = data.seed_bid || 0.99
    const seed_ask = data.seed_ask || 1.01

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    await create_assets_requests.request('create_asset', {
        ticker: ticker,
        qty: seed_qty,
        seed_price: seed_price,
        seed_bid: seed_bid,
        seed_ask: seed_ask,
    })

    res.json(create_assets_requests.latest_result)
})

const get_orderbook_requests = new Requester('5570')
app.get('/api/v1/get_order_book', async (req, res) => {
    const ticker = req.query.ticker
    const limit = parseInt(req.query.limit) || 20

    if (!ticker) { res.status(400).json({ message: 'Ticker not found.' }); return }

    await get_orderbook_requests.request('order_book', { ticker: ticker, limit: limit, })

    res.json(get_orderbook_requests.latest_result)
})

const get_latest_trade_requests = new Requester('5570')
app.get('/api/v1/get_latest_trade', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    await get_latest_trade_requests.request('latest_trade', {
        ticker: ticker,
    })

    res.json(get_latest_trade_requests.latest_result)
})

const get_trades_requests = new Requester('5570')
app.get('/api/v1/get_trades', async (req, res) => {
    const ticker = req.query.ticker
    const limit = parseInt(req.query.limit) || 20

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    await get_trades_requests.request('trades', {
        ticker: ticker,
        limit: limit,
    })

    res.json(get_trades_requests.latest_result)
})

const get_quotes_requests = new Requester('5570')
app.get('/api/v1/get_quotes', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    await get_quotes_requests.request('quotes', {
        ticker: ticker,
    })

    res.json(get_quotes_requests.latest_result)
})

const get_best_bid_requests = new Requester('5570')
app.get('/api/v1/get_best_bid', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    await get_best_bid_requests.request('best_bid', {
        ticker: ticker,
    })

    res.json(get_best_bid_requests.latest_result)
})

const get_best_ask_requests = new Requester('5570')
app.get('/api/v1/get_best_ask', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    await get_best_ask_requests.request('best_ask', {
        ticker: ticker,
    })

    res.json(get_best_ask_requests.latest_result)
})

const get_midprice_requests = new Requester('5570')
app.get('/api/v1/get_midprice', async (req, res) => {
    const ticker = req.query.ticker

    if (!ticker) {
        res.status(400).json({ message: 'Ticker not found.' })
        return
    }

    await get_midprice_requests.request('midprice', {
        ticker: ticker,
    })

    res.json({ midprice: get_midprice_requests.latest_result })
})

const limit_buy_requests = new Requester('5570')
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

    await limit_buy_requests.request('limit_buy', {
        ticker: ticker,
        price: price,
        qty: qty,
        creator: creator,
        fee: fee,
    })

    res.json(limit_buy_requests.latest_result)
})

const limit_sell_requests = new Requester('5570')
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

    await limit_sell_requests.request('limit_sell', {
        ticker: ticker,
        price: price,
        qty: qty,
        creator: creator,
        fee: fee,
    })

    res.json(limit_sell_requests.latest_result)
})

const cancel_order_requests = new Requester('5570')
app.post('/api/v1/cancel_order', async (req, res) => {
    const data = req.body
    const order_id = data.id

    if (!order_id) {
        res.status(400).json({ message: 'Order ID not found.' })
        return
    }

    await cancel_order_requests.request('cancel_order', {
        order_id: order_id,
    })

    res.json(cancel_order_requests.latest_result)
})

const cancel_all_orders_requests = new Requester('5570')
app.post('/api/v1/cancel_all_orders', async (req, res) => {
    const data = req.body
    const agent = data.agent
    const ticker = data.ticker

    if (!ticker || !agent) {
        res.status(400).json({ message: 'Invalid data. Check required fields.' })
        return
    }

    await cancel_all_orders_requests.request('cancel_all_orders', {
        ticker: ticker,
        agent: agent,
    })

    res.json(cancel_all_orders_requests.latest_result)
})

const market_buy_requests = new Requester('5570')
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

    await market_buy_requests.request('market_buy', {
        ticker: ticker,
        qty: qty,
        buyer: buyer,
        fee: fee,
    })

    res.json(market_buy_requests.latest_result)
})

const market_sell_requests = new Requester('5570')
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

    await market_sell_requests.request('market_sell', {
        ticker: ticker,
        qty: qty,
        seller: seller,
        fee: fee,
    })

    res.json(market_sell_requests.latest_result)
})

app.listen(5000, () => {
    console.log('Server started on http://localhost:5000')
})
