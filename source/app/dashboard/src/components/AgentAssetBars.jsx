import React, { useEffect, useRef } from 'react';
import * as echarts from 'echarts';


const AgentAssetBars = ({ frozen, available, asset }) => {
  const chartRef = useRef(null);

  useEffect(() => {
    const chart = echarts.init(chartRef.current);

    const options = {
      animation: false,
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'shadow',
        },
      },
      legend: {
        data: [`Frozen ${asset} ${frozen[asset] ? frozen[asset] : 0}`, `Available ${asset} ${available[asset]}`],
        bottom: 0,
      },
      grid: {
        top: '5%',
        left: '3%',
        right: '4%',
        bottom: '15%',
        containLabel: true,
      },
      xAxis: {
        type: 'category',
        data: [asset],
        position: 'top',
        axisLabel: {
          fontSize: 16,
          fontWeight: 'bold',
        },
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLine: { show: false },
        axisTick: { show: false },
        splitLine: { show: false },
      },
      series: [
        {
          name: `Frozen ${asset} ${frozen[asset]? frozen[asset] : 0}`,
          type: 'bar',
          barWidth: '100%',
          stack: 'Assets',
          data: [frozen[asset]],
        },
        {
          name: `Available ${asset} ${available[asset]}`,
          type: 'bar',
          barWidth: '100%',
          stack: 'Assets',
          data: [available[asset]],
        },
      ],
    };

    chart.setOption(options);

    return () => {
      chart.dispose();
    };
  }, [frozen, available, asset]);

  return <div ref={chartRef} style={{ width: '400px', height: '350px' }} />;
};

export default AgentAssetBars;