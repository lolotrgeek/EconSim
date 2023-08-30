import express from 'express'
import Requester from './Requester.js'
const app = express()


app.get('/', (req, res) => {
    res.send('This is the Company api.')
})

const get_date_requests = new Requester('5572')
app.get('/api/v1/get_date', async (req, res) => {
    await get_date_requests.request('get_date', {})
    res.json(get_date_requests.latest_result)
})


const get_company_list_requests = new Requester('5572')
app.get('/api/v1/get_company_list', async (req, res) => {
    await get_company_list_requests.request('get_companies', {})
    res.json(get_company_list_requests.latest_result)
})


const get_company_requests = new Requester('5572')
app.get('/api/v1/get_company', async (req, res) => {
    const company = req.query.company
    if (!company) res.status(400).json({ message: 'company not found.' })    
    await get_company_requests.request('get_company', {company})
    res.json(get_company_requests.latest_result)
})

const get_income_statement_requests = new Requester('5572')
app.get('/api/v1/get_income_statement', async (req, res) => {
    const company = req.query.company
    if (!company) res.status(400).json({ message: 'company not found.' })
    await get_income_statement_requests.request('get_income_statement', {company})
    res.json(get_income_statement_requests.latest_result)
})

const get_balance_sheet_requests = new Requester('5572')
app.get('/api/v1/get_balance_sheet', async (req, res) => {
    const company = req.query.company
    if (!company) res.status(400).json({ message: 'company not found.' })
    await get_balance_sheet_requests.request('get_balance_sheet', {company})
    res.json(get_balance_sheet_requests.latest_result)
})

const get_cash_flow_requests = new Requester('5572')
app.get('/api/v1/get_cash_flow', async (req, res) => {
    const company = req.query.company
    if (!company) res.status(400).json({ message: 'company not found.' })
    await get_cash_flow_requests.request('get_cash_flow', {company})
    res.json(get_cash_flow_requests.latest_result)
})

const get_dividend_payment_dates_requests = new Requester('5572')
app.get('/api/v1/get_dividend_payment_dates', async (req, res) => {
    const company = req.query.company
    if (!company) res.status(400).json({ message: 'company not found.' })
    await get_dividend_payment_dates_requests.request('get_dividend_payment_dates', {company})
    res.json(get_dividend_payment_dates_requests.latest_result)
})

const get_ex_dividend_dates_requests = new Requester('5572')
app.get('/api/v1/get_ex_dividend_dates', async (req, res) => {
    const company = req.query.company
    if (!company) res.status(400).json({ message: 'company not found.' })
    await get_ex_dividend_dates_requests.request('get_ex_dividend_dates', {company})
    res.json(get_ex_dividend_dates_requests.latest_result)
})


const get_dividends_to_distribute_requests = new Requester('5572')
app.get('/api/v1/get_dividends_to_distribute', async (req, res) => {
    const company = req.query.company
    if (!company) res.status(400).json({ message: 'company not found.' })
    await get_dividends_to_distribute_requests.request('get_dividends_to_distribute', {company})
    res.json(get_dividends_to_distribute_requests.latest_result)
})

app.listen(5002, () => {
    console.log('Companies API started on http://localhost:5002')
})
