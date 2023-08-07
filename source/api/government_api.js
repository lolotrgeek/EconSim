import express from 'express'
import Requester from './Requester.js'
const app = express()

app.get('/', (req, res) => {
    res.send('This is the government API.')
})

// get date endpoint
const get_date_requests = new Requester('5580')
app.get('/api/v1/get_date', async (req, res) => {
    await get_date_requests.request('get_date', {})
    res.json(get_date_requests.latest_result)
})

const get_cash_requests = new Requester('5580')
app.get('/api/v1/get_cash', async (req, res) => {
    await get_cash_requests.request('get_cash', {})
    res.json(get_cash_requests.latest_result)
})

const get_last_collected_taxes_requests = new Requester('5580')
app.get('/api/v1/get_last_collected_taxes', async (req, res) => {
    await get_last_collected_taxes_requests.request('get_last_collected_taxes', {})
    res.json(get_last_collected_taxes_requests.latest_result)
})

app.listen(5001, () => {
    console.log('Server started on http://localhost:5001')
})
