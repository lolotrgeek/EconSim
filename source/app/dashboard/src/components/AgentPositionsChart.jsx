import React, { useState, useEffect } from 'react';
import * as echarts from 'echarts';

const PositionSankey = ({ positions }) => {
  const [chart, setChart] = useState(null);

  useEffect(() => {
    if (positions.length > 0) {
      const chart = echarts.init(document.getElementById('position-sankey'));
      const nodes = [];
      const links = [];

      positions.forEach((position) => {
        const assetNode = {
          name: position.asset,
          itemStyle: { color: '#00bfff' },
        };
        nodes.push(assetNode);

        position.enters.forEach((enter) => {
          const enterNode = {
            name: enter.dt,
            itemStyle: { color: '#00bfff' },
          };
          nodes.push(enterNode);

          const link = {
            source: assetNode.name,
            target: enterNode.name,
            value: enter.qty,
          };
          links.push(link);
        });

        position.exits.forEach((exit) => {
          const exitNode = {
            name: exit.dt,
            itemStyle: { color: '#ff6347' },
          };
          nodes.push(exitNode);

          const link = {
            source: assetNode.name,
            target: exitNode.name,
            value: exit.qty,
          };
          links.push(link);
        });
      });

      const option = {
        title: {
          text: 'Position Sankey',
        },
        tooltip: {
          trigger: 'item',
          triggerOn: 'mousemove',
        },
        series: {
          type: 'sankey',
          layout: 'none',
          data: nodes,
          links: links,
          itemStyle: {
            borderWidth: 1,
            borderColor: '#aaa',
          },
          lineStyle: {
            color: 'source',
            curveness: 0.5,
          },
        },
      };

      chart.setOption(option);
      setChart(chart);
    }
  }, [positions]);

  return <div id="position-sankey" style={{ width: '100%', height: '500px' }}></div>;
};

export default PositionSankey;