import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import AgentSanKey from './AgentPositionsChart'
import { parse } from '../utils'
import '../styles/AgentPositions.css'

// TODO: update this component to paginate the positions
// the initial fetch gives looks like this:
// { agent: "agent_id", next_page: 2, page: 1, page_size: 10, positions: (1) […], total_pages: 1, total_positions: 1 }
// so you can use the next_page and total_pages to paginate the positions
const AgentPositions = () => {
    const location = useLocation()
    const agent = location.pathname.replace('/agents/', '')
    const [agentPositions, setAgentPositions] = useState([])

    useEffect(() => {

        const fetchAgentPositions = async () => {
            try {
                const response = await fetch('http://127.0.0.1:5004/api/v1/get_positions?agent=' + agent)
                if (!response.ok) throw new Error('Failed to fetch agent positions')
                const data = await response.json()
                const parsed_positions = parse(data)
                if (typeof parsed_positions == 'object' && Array.isArray(parsed_positions.positions)) setAgentPositions(parsed_positions.positions)
            } catch (error) {
                console.error(error)
            }
        }
        fetchAgentPositions()
        const interval = setInterval(fetchAgentPositions, 1000)

        return () => {
            clearInterval(interval)
        }
    }, [agent])

    return (
        <div className='positions-container '>
            <h3>Positions</h3>
            <div className="positions-header">
                <div className="position-item positions-header-item">
                    <div>ASSET/QTY</div>
                </div>
                <div className="position-item positions-header-item">
                    <div>ENTERS</div>
                </div>
                <div className="position-item positions-header-item">
                    <div>EXITS</div>
                </div>
            </div>
            {agentPositions !== undefined && agentPositions.length > 0 ? (
                <div className='agent-positions'>
                    {agentPositions.map((position, index) => (
                        <div key={index} className="position-row">
                            <div className="position-item">
                                <div>{position.asset}</div>
                                <div>{position.qty}</div>
                            </div>
                            <div className="position-item">
                                {position.enters.map((enter, index) => (
                                    <div key={index} className="enter-exit-value"> 
                                        <div>{enter.dt}</div>
                                        <div>{enter.qty}/{enter.initial_qty} </div>
                                        
                                    </div>
                                ))}
                            </div>
                            <div className="position-item">
                                <div className="enter-exit-label">Exits:</div>
                                {position.exits.map((exit, index) => (
                                    <div key={index} className="enter-exit-value">{exit.dt} - {exit.qty}</div>
                                ))}
                            </div>
                        </div>

                    ))}
                    
                </div>
            ) : (
                <p>Loading...</p>
            )}

        </div>
    )
}

export default AgentPositions
