import React from 'react'
import '../styles/AgentCard.css'

const AgentCard = ({ agent }) => {
  return (
    <div className="agent-card">
      <h3>{agent.agent}</h3>
      <p>Assets:</p>
      {typeof agent.assets == 'object' ? Object.keys(agent.assets).map((asset, index) => <p key={index}>{asset}: {agent.assets[asset]}</p>) : "None"}
    </div>
  );
};

export default AgentCard