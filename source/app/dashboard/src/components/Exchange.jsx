import React, { useEffect, useState } from 'react'
import { useLocation, useNavigate  } from 'react-router-dom'
import Financials from './Financials'
import OrderBook from './OrderBook'
import Tickers from './Tickers'
import Chart from './Chart'
import '../styles/AgentList.css'
import '../styles/Exchange.css'

const base_url = 'http://127.0.0.1:5000'

const Exchange = () => {
    const location = useLocation()
    const navigate = useNavigate()
    let ticker = location.pathname.replace('/exchange/', '')
    const [page, setPage] = useState('Exchange')
    const [time, setTime] = useState('0')
    const [tickers, setTickers] = useState([])
    const [orderBook, setOrderBook] = useState({ bids: [], asks: [] })
    const [candles, setCandles] = useState([{open: 0, high: 0, low: 0, close: 0, dt: 0}])

    useEffect(() => {
        const fetchTickerData = async () => {
            try {
                if (!ticker || ticker === '' || ticker === '/' ||  ticker === 'undefined') ticker = tickers[0]
                const orderbookUrl = `${base_url}/api/v1/get_order_book?ticker=${ticker}`
                const orderBookResponse = await fetch(orderbookUrl)
                const orderBookData = await orderBookResponse.json()
                setOrderBook(JSON.parse(orderBookData))
    
                const candlesResponse = await fetch(`${base_url}/api/v1/candles?ticker=${ticker}&interval=1M`)
                const candlesData = await candlesResponse.json()
                setCandles(JSON.parse(candlesData))                
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
        const fetchData = async () => {

            const timeResponse = await fetch(`${base_url}/api/v1/sim_time`)
            const timeData = await timeResponse.json()
            setTime(JSON.parse(timeData))
            
            const tickersResponse = await fetch(`${base_url}/api/v1/get_tickers`)
            const tickersData = await tickersResponse.json()
            const new_tickers = JSON.parse(tickersData)
            if (ticker === '' || ticker === '/') {
                navigate(`/exchange/${encodeURIComponent(new_tickers[0])}`)
            }
            setTickers( new_tickers)

        }
        const interval = setInterval(fetchData, 500)

        return () => {
            clearInterval(interval)
        }
    }, [])

    return (
        <div>
            <h1>Exchange</h1>
            <h3>{time}</h3>
            <div className="exchange-container">
                <Tickers tickers={tickers} selectedTicker={ticker} />
                <div className='exchange-content'> 
                    <div className='exchange-chart'>
                        <Chart candles={candles} />
                    </div>
                    <div className="exchange-positions">
                        <Financials />
                    </div>
                </div>

                {orderBook.bids !== undefined && orderBook.asks !== undefined ?
                    <OrderBook bids={orderBook.bids} asks={orderBook.asks} />: 
                    <p>loading...</p>
                }


                
            </div>
        </div>
    )
}
export default Exchange
