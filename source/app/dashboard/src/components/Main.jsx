import React, { useEffect, useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom'
import Exchange from './Exchange'
import Government from './Government'
import Agents from './Agents'
import '../styles/AgentList.css'
import '../styles/MainContent.css'

const base_url = 'http://127.0.0.1:5000'

const Main = () => {
    const [page, setPage] = useState('Exchange')

    return (
        <Router>
            <div className='nav-container'>
                <Link to={"/"} onClick={() => setPage("Exchange")} className={`nav-item ${page ? 'selected' : ''}`}><h2>Exchange</h2></Link>
                <Link to={"/government"} onClick={() => setPage("Government")} className={`nav-item ${page ? 'selected' : ''}`}><h2>Govnerment</h2></Link>
                <Link to={"/agents"} onClick={() => setPage("Agents")} className={`nav-item ${page ? 'selected' : ''}`}><h2>Agents</h2></Link>
            </div>


            <div className="app-container">
                <Routes>
                    <Route path="/" element={<Exchange />}></Route>
                    <Route path="/Exchange/*" element={<Exchange />}></Route>
                    <Route path="/government" element={<Government />}></Route>
                    <Route path="/agents" element={<Agents />}></Route>
                    <Route path="/agents/*" element={<Agents />}></Route>
                </Routes>
            </div>
        </Router>
    )
}
export default Main
