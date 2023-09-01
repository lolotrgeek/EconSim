import React, { useEffect, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import AgentCard from './AgentCard'
import AgentPositions from './AgentPositions'
import '../styles/AgentList.css'
import '../styles/Exchange.css'

const base_url = 'http://127.0.0.1:5000'

const Agents = () => {
    const [time, setTime] = useState('0')
    const [agents, setAgents] = useState([])

    useEffect(() => {
        const fetchData = async () => {
            const timeResponse = await fetch(`${base_url}/api/v1/sim_time`)
            const timeData = await timeResponse.json()
            setTime(JSON.parse(timeData))

            const agentsResponse = await fetch(`${base_url}/api/v1/get_agents`)
            const agentsData = await agentsResponse.json()
            setAgents(JSON.parse(agentsData))

        }
        const interval = setInterval(fetchData, 500)

        return () => {
            clearInterval(interval)
        }
    }, [])

    return (
        <div>
            <h1>Agents</h1>
            <h3>{time}</h3>
            <div className="exchange-container">
                <div className="agent-list">
                    <h1>Agent List</h1>
                    <div className="agent-cards">
                        {Array.isArray(agents) ? agents.map((agent, index) => (
                            <Link key={index} to={`/agents/${encodeURIComponent(agent.agent)}`}>
                                <AgentCard agent={agent} />
                            </Link>
                        )) : 
                        <p>loading...</p>
                        }
                    </div>
                </div>
                <div className='exchange-content'> 
                    <div className="exchange-positions">
                        {useLocation().pathname === '/agents' ?
                        <div>Press an agent to view Positions here.</div> : 
                        <AgentPositions />
                        }
                    </div>
                </div>
            </div>
        </div>
    )
}
export default Agents
