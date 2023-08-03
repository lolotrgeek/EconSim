import React from 'react'

const AgentCard = ({ agent }) => {
  return (
    <div className="agent-card">
      <h3>{agent.agent}</h3>
      <p>Assets: {JSON.stringify(agent.assets)}</p>
      <p>Net Worth: {agent.cash}</p>
    </div>
  );
};

export default AgentCard