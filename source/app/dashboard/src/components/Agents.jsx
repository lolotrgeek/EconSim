import React, { useEffect, useState } from 'react'
import { useLocation, Link } from 'react-router-dom'
import AgentCard from './AgentCard'
import AgentPositions from './AgentPositions'
import AgentAssetBars from './AgentAssetBars'
import {parse} from '../utils'
import '../styles/AgentList.css'
import '../styles/Agents.css'

const base_url = 'http://127.0.0.1:5004'

const Agents = () => {
    const [agents, setAgents] = useState([])
    const [agent, setAgent] = useState({})

    useEffect(() => {
        const fetchData = async () => {
            const agentsResponse = await fetch(`${base_url}/api/v1/get_agents`)
            const agentsData = await agentsResponse.json()
            const parsed_agents = parse(agentsData)
            if(Array.isArray(parsed_agents)) setAgents(parsed_agents)
        }
        const interval = setInterval(fetchData, 500)

        return () => {
            clearInterval(interval)
        }
    }, [])

    return (
        <div className="agents-page">
            <div className="agents-container">
                <div className="agent-list">
                    <h1>Agents</h1>
                    <div className="agent-cards">
                        {agents.length > 0 ? agents.map((agent, index) => (
                            <Link key={index} to={`/agents/${encodeURIComponent(agent.agent)}`} onClick={() => setAgent(agent)}>
                                <AgentCard agent={agent} />
                            </Link>
                        )) : 
                        <p>loading...</p>
                        }
                    </div>
                </div>
                <div className='agents-content'>
                    <h2>{agent.agent ? agent.agent : "Agents"}</h2> 
                    <div className="agents-positions">
                        {useLocation().pathname === '/agents' ?
                        <div>Press an agent to view Positions here.</div> : 
                        <AgentPositions />
                        }
                    </div>
                    <div className='asset-bars'>
                        {agent.agent && agent.frozen_assets && agent.assets ?
                        Object.keys({...agent.assets, ...agent.frozen_assets}).map((asset, index) => (
                            <AgentAssetBars key={index} asset={asset} frozen={agent.frozen_assets} available={agent.assets} />
                        )) :
                         <p>loading...</p>}
                    </div>               
                </div>
            </div>
        </div>
    )
}
export default Agents
