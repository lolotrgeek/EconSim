import React, { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Exchange from './Exchange'
import Government from './Government'
import Agents from './Agents'
import '../styles/MainContent.css'

const base_url = 'http://127.0.0.1:5004'

const Main = () => {
    const [page, setPage] = useState('Exchange')
    const [time, setTime] = useState('0')

    useEffect(() => {
        const fetchData = async () => {
            const timeResponse = await fetch(`${base_url}/api/v1/sim_time`)
            const timeData = await timeResponse.json()
            setTime(JSON.parse(timeData))
        }   
        const interval = setInterval(fetchData, 500)
        
        return () => {
            clearInterval(interval)
        }
    }, [])

    return (
        <Router>
            <div className='nav-container'>
                <Link to={"/exchange/"} onClick={() => setPage("Exchange")} className={`nav-item ${page == 'Exchange' ? 'selected' : ''}`}><h2>Exchange</h2></Link>
                <Link to={"/government"} onClick={() => setPage("Government")} className={`nav-item ${page =='Government' ? 'selected' : ''}`}><h2>Govnerment</h2></Link>
                <Link to={"/agents"} onClick={() => setPage("Agents")} className={`nav-item ${page == 'Agents' ? 'selected' : ''}`}><h2>Agents</h2></Link>
                <div className="nav-item time"><h3>{time}</h3></div>
            </div>


            <div className="app-container">
                <Routes>
                    <Route path="/" element={<div>Welcome!</div>}></Route>
                    <Route path="/exchange" element={<Exchange />}></Route>
                    <Route path="/exchange/*" element={<Exchange />}></Route>
                    <Route path="/government" element={<Government />}></Route>
                    <Route path="/agents" element={<Agents />}></Route>
                    <Route path="/agents/*" element={<Agents />}></Route>
                </Routes>
            </div>
        </Router>
    )
}
export default Main
