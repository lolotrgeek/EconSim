import express from 'express'
import Requester from './Requester.js'
const app = express()


app.get('/', (req, res) => {
    res.send('This is the Crypto api.')
})

const get_transactions = new Requester('5571')
app.get('/api/v1/get_transactions', async (req, res) => {
    const asset = req.query.asset
    await get_transactions.request('get_transactions', {asset})
    res.json(get_transactions.latest_result)
})

const get_mempool = new Requester('5571')
app.get('/api/v1/get_mempool', async (req, res) => {
    const asset = req.query.asset
    await get_mempool.request('get_mempool', {asset})
    res.json(get_mempool.latest_result)
})

app.listen(5003, () => {
    console.log('Crypto API started on http://localhost:5003')
})
