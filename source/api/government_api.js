import express from 'express'
import Subscriber from './Subscriber.js'
const app = express()

const PORT = 5001
const URL = 'http://localhost:'+PORT

const endpoints = {
    get_date: '/api/v1/get_date',
    get_cash: '/api/v1/get_cash',
    get_last_collected_taxes: '/api/v1/get_last_collected_taxes',
    get_taxes_collected: '/api/v1/get_taxes_collected',
    get_back_taxes: '/api/v1/get_back_taxes',

}

app.get('/', (req, res) => {
    const title = '<p>This is the Government API. It is used to get information from the Government.</p>'
    const endpoints_html = `<p>Available endpoints:</p> ${Object.values(endpoints).map(endpoint => `<p><a href="${URL}${endpoint}">${endpoint}</a></p>`).join('')}`
    res.send(title + endpoints_html)
})

const get_date_pulls = new Subscriber('5580')
app.get(endpoints.get_date, async (req, res) => {
    await get_date_pulls.pull('get_date')
    res.json(get_date_pulls.latest_result)
})

const get_cash_pulls = new Subscriber('5580')
app.get(endpoints.get_cash, async (req, res) => {
    await get_cash_pulls.pull('get_cash')
    res.json(get_cash_pulls.latest_result)
})

const get_last_collected_taxes_pulls = new Subscriber('5580')
app.get(endpoints.get_last_collected_taxes, async (req, res) => {
    await get_last_collected_taxes_pulls.pull('get_last_collected_taxes')
    res.json(get_last_collected_taxes_pulls.latest_result)
})

const get_taxes_collected_pulls = new Subscriber('5580')
app.get(endpoints.get_taxes_collected, async (req, res) => {
    await get_taxes_collected_pulls.pull('get_taxes_collected')
    res.json(get_taxes_collected_pulls.latest_result)
})

const get_back_taxes_pulls = new Subscriber('5580')
app.get(endpoints.get_back_taxes, async (req, res) => {
    await get_back_taxes_pulls.pull('get_back_taxes')
    res.json(get_back_taxes_pulls.latest_result)
})

app.listen(PORT, () => {
    console.log('Government API started on http://localhost:'+PORT)
})
