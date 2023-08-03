import React from 'react';
import { List } from 'react-virtualized';
import AgentCard from './AgentCard';

const AgentList = ({ agents }) => {
  const rowRenderer = ({ index, key, style }) => {
    const agent = agents[index];

    return (
      <div key={key} style={style}>
        <AgentCard agent={agent} />
      </div>
    );
  };

  return (
    <div className="agent-list">
        <h2>Agents</h2>
      <List
        height={400} // Set the height of the scrollable area
        width={300} // Set the width of the list
        rowCount={agents.length}
        rowHeight={100} // Set the height of each row (agent card)
        rowRenderer={rowRenderer}
      />
    </div>
  );
};

export default AgentList;