import React from 'react';
import '../styles/OrderBook.css';
import { CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend, Chart } from "chart.js";
import { Bar } from 'react-chartjs-2';

Chart.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);


const OrderBook = ({ bids, asks }) => (
  <div className="order-book">
    <div className="bids">
      <h2>Bids</h2>
      <div className="bids-list">
        <div className="table-row header">
          <div>Time</div>
          <div>Price</div>
          <div>Quantity</div>
        </div>
        {bids.map((entry, index) => (
          <div className="table-row" key={index}>
            <div>{entry.dt}</div>
            <div>{entry.price}</div>
            <div>{entry.qty}</div>
          </div>
        ))}
      </div>
    </div>
    <div className="asks">
      <h2>Asks</h2>
      <div className="asks-list">
        <div className="table-row header">
          <div>Time</div>
          <div>Price</div>
          <div>Quantity</div>
        </div>
        {asks.map((entry, index) => (
          <div className="table-row" key={index}>
            <div>{entry.dt}</div>
            <div>{entry.price}</div>
            <div>{entry.qty}</div>
          </div>
        ))}
      </div>
    </div>
  </div>
)

// const OrderBook = ({ bids, asks }) => {
//   // Extract price and cumulative qty for bids and asks
//   const bidPrices = bids.map((bid) => bid.price);
//   const bidCumulativeQuantities = bids
//     .map((bid) => bid.qty)
//     .reduce((acc, qty, index) => {
//       acc.push((acc[index - 1] || 0) + qty);
//       return acc;
//     }, []);

//   const askPrices = asks.map((ask) => ask.price);
//   const askCumulativeQuantities = asks
//     .map((ask) => ask.qty)
//     .reduce((acc, qty, index) => {
//       acc.push((acc[index - 1] || 0) + qty);
//       return acc;
//     }, []);

//   const data = {
//     labels: [...Array(bidPrices.length).keys(), ...Array(askPrices.length).keys()],
//     datasets: [
//       {
//         label: 'Bids',
//         data: [...bidCumulativeQuantities, ...Array(askPrices.length).fill(0)],
//         backgroundColor: 'green',
//       },
//       {
//         label: 'Asks',
//         data: [...Array(bidPrices.length).fill(0), ...askCumulativeQuantities],
//         backgroundColor: 'red',
//       },
//     ],
//   };

//   const options = {
//     indexAxis: 'y', // Display data on the y-axis
//     scales: {
//       y: {
//         type: 'category', // Use "category" scale for y-axis
//         beginAtZero: true, // Start y-axis from 0
//         reverse: true, // Reverse the y-axis to match traditional order book layout
//       },
//     },
//     plugins: {
//       legend: {
//         display: true,
//         position: 'top',
//       },
//       tooltip: {
//         mode: 'index',
//         intersect: false,
//       },
//     },
//   };

//   return (
//     <div className="depth-chart">
//       <Bar data={data} options={options} />
//     </div>
//   );
// };

export default OrderBook;