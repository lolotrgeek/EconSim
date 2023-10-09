import express from 'express'
import Requester from './Requester.js'
const app = express()

const PORT = 5003
const URL = 'http://localhost:'+PORT

const endpoints = {
    get_transactions: '/api/v1/get_transactions',
    get_mempool: '/api/v1/get_mempool'
}

app.get('/', (req, res) => {
    const title = '<p>This is the Crypto API. It is used to get information from the Crypto.</p>'
    endpoints_html = `<p>Available endpoints:</p> ${Object.values(endpoints).map(endpoint => `<p><a href="${URL}${endpoint}">${endpoint}</a></p>`).join('')}`
    res.send(title + endpoints_html)
})

const get_transactions = new Requester('5571')
app.get(endpoints.get_transactions, async (req, res) => {
    const asset = req.query.asset
    await get_transactions.request('get_transactions', {asset})
    res.json(get_transactions.latest_result)
})

const get_mempool = new Requester('5571')
app.get(endpoints.get_mempool, async (req, res) => {
    const asset = req.query.asset
    await get_mempool.request('get_mempool', {asset})
    res.json(get_mempool.latest_result)
})

app.listen(PORT, () => {
    console.log('Crypto API started on http://localhost:'+PORT)
})
