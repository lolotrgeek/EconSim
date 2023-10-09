import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import {parse} from '../utils'
import OrderBook from './OrderBook'
import Tickers from './Tickers'
import Chart from './Chart'
import '../styles/AgentList.css'
import '../styles/Exchange.css'

const base_url = 'http://127.0.0.1:5004'

const Exchange = () => {
    const location = useLocation()
    const navigate = useNavigate()
    let ticker = location.pathname.replace('/exchange/', '')
    const [tickers, setTickers] = useState([])
    const [orderBook, setOrderBook] = useState({ bids: [], asks: [] })
    const [candles, setCandles] = useState([{ open: 0, high: 0, low: 0, close: 0, dt: 0 }])

    useEffect(() => {
        const fetchTickerData = async () => {
            try {
                const orderbookUrl = `${base_url}/api/v1/get_order_book?ticker=${ticker}`
                const orderBookResponse = await fetch(orderbookUrl)
                const orderBookData = await orderBookResponse.json()
                setOrderBook(parse(orderBookData))

                const candlesResponse = await fetch(`${base_url}/api/v1/candles?ticker=${ticker}&interval=1M`)
                const candlesData = await candlesResponse.json()
                const parsedCandles = parse(candlesData)
                if (Array.isArray(parsedCandles) && parsedCandles.length > 0) setCandles(parsedCandles)
                
            } catch (error) {
                console.log(error)
            }
        }
        fetchTickerData()
        const interval = setInterval(fetchTickerData, 500)

        return () => {
            clearInterval(interval)
        }
    }, [ticker])

    useEffect(() => {
        const fetchTickers = async () => {
            const tickersResponse = await fetch(`${base_url}/api/v1/get_tickers`)
            const tickersData = await tickersResponse.json()
            console.log(tickersData)
            const new_tickers = parse(tickersData)
            console.log(new_tickers)
            if (Array.isArray( new_tickers)) {
                const tickers = new_tickers.map(ticker => `${ticker.base}${ticker.quote}`)
                setTickers(tickers)
                if (!ticker || ticker === '' || ticker === '/' || ticker === 'undefined') {
                    navigate(`/exchange/${encodeURIComponent(tickers[0])}`)
                }                
            }
        }
        fetchTickers()
        
    }, [])

    return (
        <div>
            <h1>Exchange</h1>
            <div className="exchange-container">
                <Tickers tickers={tickers} selectedTicker={ticker} />
                <div className='exchange-content'>
                    <div className='exchange-chart'>
                        <Chart candles={candles} />
                    </div>
                </div>

                {orderBook.bids !== undefined && orderBook.asks !== undefined ?
                    <OrderBook bids={orderBook.bids} asks={orderBook.asks} /> :
                    <p>loading...</p>
                }
            </div>
        </div>
    )
}
export default Exchange
