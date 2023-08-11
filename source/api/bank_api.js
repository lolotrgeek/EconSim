import express from 'express'
import Puller from './Puller.js'
import Requester from './Requester.js'
const app = express()

const bank_response_channel = 5582
const bank_channel= 5581

app.get('/', (req, res) => {
    res.send('This is the Bank API.')
})

const get_date_pulls = new Puller(bank_channel)
app.get('/api/v1/get_date', async (req, res) => {
    await get_date_pulls.pull('get_date')
    res.json(get_date_pulls.latest_result)
})

const get_reserve_pulls = new Puller(bank_channel)
app.get('/api/v1/get_reserve', async (req, res) => {
    await get_reserve_pulls.pull('get_reserve')
    res.json(get_reserve_pulls.latest_result)
})

const get_loans = new Puller(bank_channel)
app.get('/api/v1/get_loans', async (req, res) => {
    await get_loans.pull('get_loans')
    res.json(get_loans.latest_result)
})

const get_deposits = new Puller(bank_channel)
app.get('/api/v1/get_deposits', async (req, res) => {
    await get_deposits.pull('get_deposits')
    res.json(get_deposits.latest_result)
})

const get_accounts = new Puller(bank_channel)
app.get('/api/v1/get_accounts', async (req, res) => {
    await get_accounts.pull('get_accounts')
    res.json(get_accounts.latest_result)
})

const get_prime_rate = new Puller(bank_channel)
app.get('/api/v1/get_prime_rate', async (req, res) => {
    await get_prime_rate.pull('get_prime_rate')
    res.json(get_prime_rate.latest_result)
})

const get_credit_scores = new Puller(bank_channel)
app.get('/api/v1/get_credit_scores', async (req, res) => {
    await get_credit_scores.pull('get_credit')
    res.json(get_credit_scores.latest_result)
})

app.listen(5003, () => {
    console.log('Server started on http://localhost:5003')
})
