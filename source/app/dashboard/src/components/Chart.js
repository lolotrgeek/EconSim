import React, { useState, useEffect } from 'react';
import ApexCharts from 'react-apexcharts';

const CandlestickChart = () => {
  const [chartData, setChartData] = useState({
    options: {
      chart: {
        type: 'candlestick',
        height: 400,
      },
      xaxis: {
        type: 'category',
      },
      yaxis: {
        tooltip: {
          enabled: true,
        },
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
    const fetchData = () => {
      fetch('http://127.0.0.1:5000/api/v1/candles?ticker=XYZ')
        .then((response) => response.json())
        .then(data => {
          // Assuming the API response contains OHLCV data in the format mentioned earlier
          const ohlcvData = JSON.parse(data)
          console.log(typeof ohlcvData)
          setChartData((prevChartData) => ({
            ...prevChartData,
            series: [
              {
                ...prevChartData.series[0],
                data: ohlcvData.map((dataPoint) => ({
                  x: new Date(dataPoint.dt).getTime(),
                  y: [dataPoint.open, dataPoint.high, dataPoint.low, dataPoint.close],
                })),
              },
            ],
          }));
        })
        .catch((error) => {
          console.error('Error fetching data:', error);
        });
    };

    const fetchDataInterval = setInterval(fetchData, 1000);

    return () => {
      // Clear the interval when the component is unmounted to prevent memory leaks
      clearInterval(fetchDataInterval);
    };
  }, []);

  return (
    <ApexCharts options={chartData.options} series={chartData.series} type="candlestick" height={400} />
  );
};

export default CandlestickChart;
