import React, { useEffect, useState } from 'react'
import AgentList from './components/AgentList'
import OrderBook from './components/OrderBook'

const base_url = 'http://127.0.0.1:5000'

const TableComponent = ({ ticker }) => {
    const [agents, setAgents] = useState([])
    const [latestTrade, setLatestTrade] = useState({})
    const [candles, setCandles] = useState([])
    const [orderBook, setOrderBook] = useState({bids:[], asks:[]})
    const [trades, setTrades] = useState([])
    const [quotes, setQuotes] = useState({})
    const [bestBid, setBestBid] = useState({})
    const [bestAsk, setBestAsk] = useState({})
    const [midprice, setMidprice] = useState('')

    useEffect(() => {
        const fetchData = async () => {
            const agentsResponse = await fetch(`${base_url}/api/v1/get_agents`)
            const agentsData = await agentsResponse.json()
            setAgents(agentsData)

            // const getLatestTrade = await fetch(`${base_url}/api/v1/get_latest_trade?ticker=${ticker}`)
            // const getLatestTradeData = await getLatestTrade.json()
            // setLatestTrade(getLatestTradeData)

            // const candleResponse = await fetch(`${base_url}/api/v1/candles?ticker=${ticker}`)
            // const candleData = await candleResponse.json()
            // console.log(candleData)
            // setCandles(candleData)

            const orderBookResponse = await fetch(`${base_url}/api/v1/get_order_book?ticker=${ticker}`)
            const orderBookData = await orderBookResponse.json()
            setOrderBook(orderBookData)

            // const tradesResponse = await fetch(`${base_url}/api/v1/get_trades?ticker=${ticker}`)
            // const tradesData = await tradesResponse.json()
            // setTrades(tradesData)

            // const quotesResponse = await fetch(`${base_url}/api/v1/get_quotes?ticker=${ticker}`)
            // const quotesData = await quotesResponse.json()
            // setQuotes(quotesData)

            // const bestBidResponse = await fetch(`${base_url}/api/v1/get_best_bid?ticker=${ticker}`)
            // const bestBidData = await bestBidResponse.json()
            // setBestBid(bestBidData)

            // const bestAskResponse = await fetch(`${base_url}/api/v1/get_best_ask?ticker=${ticker}`)
            // const bestAskData = await bestAskResponse.json()
            // setBestAsk(bestAskData)

            // const midpriceResponse = await fetch(`${base_url}/api/v1/get_midprice?ticker=${ticker}`)
            // const midpriceData = await midpriceResponse.json()
            // setMidprice(midpriceData)
        }
        const interval = setInterval(fetchData, 1000)

        return () => {
            clearInterval(interval)
        }
    }, [ticker])

    return (
        <div>
        <div className="agent-cards">
            <AgentList agents={agents} />
        </div>
            <OrderBook bids={orderBook.bids} asks={orderBook.asks} />
        </div>
    )
}
export default TableComponent
