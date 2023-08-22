import React, { useState, useEffect } from 'react';
import ApexCharts from 'react-apexcharts';

const theme =  {
  mode: 'dark'
}

const CandlestickChart = ({candles}) => {
  const [chartData, setChartData] = useState({
    options: {
      chart: {
        type: 'candlestick',
        height: 600,
        id: 'candles',
        toolbar: {
          autoSelected: 'pan',
          show: false
        },
        zoom: {
          enabled: false
        },
      },
      plotOptions: {
        candlestick: {
          colors: {
            upward: '#3C90EB',
            downward: '#DF7D46'
          }
        }
      },
      xaxis: {
        type: 'datetime'
      },
      tooltip: {
        enabled: true,
        theme: 'dark',
      },
    },
    series: [
      {
        name: 'candle',
        data: [],
      },
    ],

  });

  useEffect(() => {

        setChartData((prevChartData) => ({
          ...prevChartData,
          series: [
            {
              ...prevChartData.series[0],
              data: candles.map((dataPoint) => ({
                x: new Date(dataPoint.dt).getTime(),
                y: [dataPoint.open, dataPoint.high, dataPoint.low, dataPoint.close],
              })),
            },
          ],
        }))
  }, [candles])

  return (
    <ApexCharts options={chartData.options} series={chartData.series} type="candlestick" height={600} width={1000} />
  );
};

export default CandlestickChart;
