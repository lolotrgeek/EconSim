import React from 'react'
import '../styles/AgentCard.css'

const AgentCard = ({ agent }) => {
  return (
    <div className="agent-card">
      <h3>{agent.agent}</h3>
      <p>Assets: {JSON.stringify(agent.assets)}</p>
      <p>Cash: {agent.cash}</p>
    </div>
  );
};

export default AgentCard