import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'
import '../styles/AgentPositions.css'

const AgentPositions = () => {
    const location = useLocation()
    const agent = location.pathname.replace('/agent/', '')
    const [agentPositions, setAgentPositions] = useState([])

    useEffect(() => {
        
        const fetchAgentPositions = async () => {
            try {
                const response = await fetch('http://127.0.0.1:5000/api/v1/get_positions?agent='+agent)
                if (!response.ok) {
                    throw new Error('Failed to fetch agent positions')
                }
                const data = await response.json()
                setAgentPositions(JSON.parse(data).positions)
            } catch (error) {
                console.error(error)
            }
        }

        const interval = setInterval(fetchAgentPositions, 1000)

        return () => {
            clearInterval(interval)
        }
    }, [agent])

    return (
        <div>
            <h2>{location.pathname.replace('/agent/', '')} Positions</h2>
            { agentPositions !== undefined && agentPositions.length > 0 ? (
                <ul className='agent-positions'>
                    {agentPositions.map((position, index) => (
                    <li key={index}>
                        {position.ticker}: {position.qty} : {position.dt} {position.enters.map(enter => (JSON.stringify(enter)))} : {position.exits.map(exit => (JSON.stringify(exit)))}
                    </li>
                    ))}
                </ul>
            ) : (
                <p>Loading...</p>
            )}
        </div>
    )
}

export default AgentPositions
