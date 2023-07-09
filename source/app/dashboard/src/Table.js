import React, { useEffect, useState } from 'react'

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
            // const agentsResponse = await fetch(`${base_url}/api/v1/get_agents`)
            // const agentsData = await agentsResponse.json()
            // setAgents(agentsData)

            const getLatestTrade = await fetch(`${base_url}/api/v1/get_latest_trade?ticker=${ticker}`)
            const getLatestTradeData = await getLatestTrade.json()
            setLatestTrade(getLatestTradeData)

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
            <h2>Latest Trade</h2>
            <table>
                <thead>
                    <tr>
                        <th>Price</th>
                        <th>Size</th>
                        <th>Time</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{latestTrade.price}</td>
                        <td>{latestTrade.qty}</td>
                        <td>{latestTrade.dt}</td>
                    </tr>
                </tbody>
            </table>
            {/* <h2>Agents</h2> */}
            {/* <table>
                <thead>
                    <tr>
                        <th>Agent</th>
                        <th>Assets</th>
                        <th>Net Worth</th>
                        <th>Orders</th>
                    </tr>
                </thead>
                <tbody>
                    {agents.map((agent, index) => (
                        <tr key={index}>
                            <td>{agent.name}</td>
                            <td>{JSON.stringify(agent.assets)}</td>
                            <td>{agent.cash}</td>
                        </tr>
                    ))}
                </tbody>
            </table> */}
            {/* <table>
                <thead>
                    <tr>
                        <th>Candles</th>
                    </tr>
                </thead>
                <tbody>
                    {candles.map((candle, index) => (
                        <tr key={index}>
                            <td>{JSON.stringify(candle)}</td>
                        </tr>
                    ))}
                </tbody>
            </table> */}
                        <h2>Order Book</h2>
            <table>
                <thead>
                    <tr>
                        <th>Bids</th>
                    </tr>
                </thead>
                <tbody>
                    {orderBook.bids.map((entry, index) => (
                        <tr key={index}>
                            <td>{JSON.stringify(entry)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <table>
            <thead>
                    <tr>
                        <th>Asks</th>
                    </tr>
                </thead>
                <tbody>
                    {orderBook.asks.map((entry, index) => (
                        <tr key={index}>
                            <td>{JSON.stringify(entry)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <table>
                <thead>
                    <tr>
                        <th>Trades</th>
                    </tr>
                </thead>
                <tbody>
                    {trades.map((trade, index) => (
                        <tr key={index}>
                            <td>{JSON.stringify(trade)}</td>
                        </tr>
                    ))}
                </tbody>
            </table>

            <table>
                <thead>
                    <tr>
                        <th>Quotes</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{JSON.stringify(quotes)}</td>
                    </tr>
                </tbody>
            </table>

            <table>
                <thead>
                    <tr>
                        <th>Best Bid</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{JSON.stringify(bestBid)}</td>
                    </tr>
                </tbody>
            </table>

            <table>
                <thead>
                    <tr>
                        <th>Best Ask</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{JSON.stringify(bestAsk)}</td>
                    </tr>
                </tbody>
            </table>

            <table>
                <thead>
                    <tr>
                        <th>Midprice</th>
                    </tr>
                </thead>
                <tbody>
                    <tr>
                        <td>{JSON.stringify(midprice)}</td>
                    </tr>
                </tbody>
            </table>
        </div>
    )
}

export default TableComponent
