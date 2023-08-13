import express from 'express'
import Requester from './Requester.js'
const app = express()


app.get('/', (req, res) => {
    res.send('This is the Company api.')
})

const get_date_requests = new Requester('5572')
app.get('/api/v1/get_date', async (req, res) => {
    await get_date_requests.pull('get_date')
    res.json(get_date_requests.latest_result)
})

