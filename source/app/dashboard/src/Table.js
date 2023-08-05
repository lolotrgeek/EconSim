import React, { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import AgentCard from './components/AgentCard';
import AgentPositions from './components/AgentPositions';
import OrderBook from './components/OrderBook'
import Chart from './components/Chart'
import './styles/AgentList.css';
import './styles/MainContent.css';

const base_url = 'http://127.0.0.1:5000'

const TableComponent = ({ ticker }) => {
    const [agents, setAgents] = useState([])
    const [currentAgent, setCurrentAgent] = useState('')
    const [latestTrade, setLatestTrade] = useState({})
    const [candles, setCandles] = useState([])
    const [orderBook, setOrderBook] = useState({ bids: [], asks: [] })
    const [trades, setTrades] = useState([])
    const [quotes, setQuotes] = useState({})
    const [bestBid, setBestBid] = useState({})
    const [bestAsk, setBestAsk] = useState({})
    const [midprice, setMidprice] = useState('')

    useEffect(() => {
        const fetchData = async () => {
            const agentsResponse = await fetch(`${base_url}/api/v1/get_agents`)
            const agentsData = await agentsResponse.json()
            setAgents(JSON.parse(agentsData))

            const orderBookResponse = await fetch(`${base_url}/api/v1/get_order_book?ticker=${ticker}`)
            const orderBookData = await orderBookResponse.json()
            setOrderBook(JSON.parse(orderBookData))

        }
        const interval = setInterval(fetchData, 500)

        return () => {
            clearInterval(interval)
        }
    }, [ticker])

    return (
        <Router>
            <Link to={"/"}><h1>Dashboard</h1></Link>
            <div className="app-container">
            
                <div className="agent-list">
                    <h1>Agent List</h1>
                    <div className="agent-cards">
                        {Array.isArray(agents) ? agents.map((agent, index) => (
                            <Link key={index} to={`/agent/${encodeURIComponent(agent.agent)}`} onClick={() => setCurrentAgent(agent.agent)}>
                                <AgentCard agent={agent} />
                            </Link>
                        )) : 
                        <p>loading...</p>
                        }
                    </div>
                </div>
                <div className="main-content">
                    <Routes>
                        {/* <Route path="/" element={<Chart />}></Route> */}
                        <Route path="/" element={<div>Press an agent to view Positions here.</div>}></Route>
                        <Route path="/agent/:agentName" element={<AgentPositions />}></Route>
                    </Routes>
                </div>
                {orderBook.bids !== undefined && orderBook.asks !== undefined ?
                    <OrderBook bids={orderBook.bids} asks={orderBook.asks} />: 
                    <p>loading...</p>
                }
                
            </div>
        </Router>
    )
}
export default TableComponent
