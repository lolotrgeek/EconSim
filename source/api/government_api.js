import express from 'express'
import Puller from './Puller.js'
const app = express()

app.get('/', (req, res) => {
    res.send('This is the government API.')
})

const get_date_pulls = new Puller('5580')
app.get('/api/v1/get_date', async (req, res) => {
    await get_date_pulls.pull('get_date')
    res.json(get_date_pulls.latest_result)
})

const get_cash_pulls = new Puller('5580')
app.get('/api/v1/get_cash', async (req, res) => {
    await get_cash_pulls.pull('get_cash')
    res.json(get_cash_pulls.latest_result)
})

const get_last_collected_taxes_pulls = new Puller('5580')
app.get('/api/v1/get_last_collected_taxes', async (req, res) => {
    await get_last_collected_taxes_pulls.pull('get_last_collected_taxes')
    res.json(get_last_collected_taxes_pulls.latest_result)
})

const get_taxes_collected_pulls = new Puller('5580')
app.get('/api/v1/get_taxes_collected', async (req, res) => {
    await get_taxes_collected_pulls.pull('get_taxes_collected')
    res.json(get_taxes_collected_pulls.latest_result)
})

app.listen(5001, () => {
    console.log('Government API started on http://localhost:5001')
})
