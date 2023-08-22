import React, { useEffect, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import AgentCard from './AgentCard'
import AgentPositions from './AgentPositions'
import OrderBook from './OrderBook'
import Tickers from './Tickers'
import Chart from './Chart'
import '../styles/AgentList.css'
import '../styles/Exchange.css'

const base_url = 'http://127.0.0.1:5000'

const Exchange = () => {
    const [page, setPage] = useState('Exchange')
    const [time, setTime] = useState('0')
    const [agents, setAgents] = useState([])
    const [tickers, setTickers] = useState([])
    const [ticker, setTicker] = useState('')
    const [orderBook, setOrderBook] = useState({ bids: [], asks: [] })
    const [candles, setCandles] = useState([{open: 0, high: 0, low: 0, close: 0, dt: 0}])

    useEffect(() => {
        const fetchTickerData = async () => {
            if (!ticker || ticker == '') return
            const orderBookResponse = await fetch(`${base_url}/api/v1/get_order_book?ticker=${ticker == '' ? tickers[0] : ticker}`)
            const orderBookData = await orderBookResponse.json()
            setOrderBook(JSON.parse(orderBookData))

            const candlesResponse = await fetch(`${base_url}/api/v1/candles?ticker=${ticker == '' ? tickers[0] : ticker}`)
            const candlesData = await candlesResponse.json()
            setCandles(JSON.parse(candlesData))

        }
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

            const agentsResponse = await fetch(`${base_url}/api/v1/get_agents`)
            const agentsData = await agentsResponse.json()
            setAgents(JSON.parse(agentsData))
            
            const tickersResponse = await fetch(`${base_url}/api/v1/get_tickers`)
            const tickersData = await tickersResponse.json()
            const new_tickers = JSON.parse(tickersData)
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
                <div className="agent-list">
                    <h1>Agent List</h1>
                    <div className="agent-cards">
                        {Array.isArray(agents) ? agents.map((agent, index) => (
                            <Link key={index} to={`/exchange/agent/${encodeURIComponent(agent.agent)}`}>
                                <AgentCard agent={agent} />
                            </Link>
                        )) : 
                        <p>loading...</p>
                        }
                    </div>
                </div>
                <div className='exchange-content'> 
                    <div className='exchange-chart'>
                        <Chart candles={candles} />
                    </div>
                    <div className="exchange-positions">
                        {useLocation().pathname === '/' ?
                        <div>Press an agent to view Positions here.</div> : 
                        <AgentPositions />
                        }
                    </div>
                </div>

                <Tickers tickers={tickers} selectedTicker={ticker} onTickerSelect={setTicker} />
                
                {orderBook.bids !== undefined && orderBook.asks !== undefined ?
                    <OrderBook bids={orderBook.bids} asks={orderBook.asks} />: 
                    <p>loading...</p>
                }
                
            </div>
        </div>
    )
}
export default Exchange
