import express from 'express'
import Puller from './Puller.js'
import Requester from './Requester.js'
const app = express()

const bank_response_channel = 5582
const bank_channel= 5581

const PORT = 5003
const URL = 'http://localhost:'+PORT

const endpoints = {
    get_date: '/api/v1/get_date',
    get_reserve: '/api/v1/get_reserve',
    get_loans: '/api/v1/get_loans',
    get_deposits: '/api/v1/get_deposits',
    get_accounts: '/api/v1/get_accounts',
    get_prime_rate: '/api/v1/get_prime_rate',
    get_credit_scores: '/api/v1/get_credit_scores'
}

app.get('/', (req, res) => {
    const title = '<p>This is the Bank API. It is used to get information from the Bank.</p>'
    const endpoints_html = `<p>Available endpoints:</p> ${Object.values(endpoints).map(endpoint => `<p><a href="${URL}${endpoint}">${endpoint}</a></p>`).join('')}`
    res.send(title + endpoints_html)
})

const get_date_pulls = new Puller(bank_channel)
app.get(endpoints.get_date, async (req, res) => {
    await get_date_pulls.pull('get_date')
    res.json(get_date_pulls.latest_result)
})

const get_reserve_pulls = new Puller(bank_channel)
app.get(endpoints.get_reserve, async (req, res) => {
    await get_reserve_pulls.pull('get_reserve')
    res.json(get_reserve_pulls.latest_result)
})

const get_loans = new Puller(bank_channel)
app.get(endpoints.get_loans, async (req, res) => {
    await get_loans.pull('get_loans')
    res.json(get_loans.latest_result)
})

const get_deposits = new Puller(bank_channel)
app.get(endpoints.get_deposits, async (req, res) => {
    await get_deposits.pull('get_deposits')
    res.json(get_deposits.latest_result)
})

const get_accounts = new Puller(bank_channel)
app.get(endpoints.get_accounts, async (req, res) => {
    await get_accounts.pull('get_accounts')
    res.json(get_accounts.latest_result)
})

const get_prime_rate = new Puller(bank_channel)
app.get(endpoints.get_prime_rate, async (req, res) => {
    await get_prime_rate.pull('get_prime_rate')
    res.json(get_prime_rate.latest_result)
})

const get_credit_scores = new Puller(bank_channel)
app.get(endpoints.get_credit_scores, async (req, res) => {
    await get_credit_scores.pull('get_credit')
    res.json(get_credit_scores.latest_result)
})

app.listen(PORT, () => {
    console.log('Server started on http://localhost:'+PORT)
})
