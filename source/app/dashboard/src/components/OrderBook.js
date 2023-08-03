import React from 'react';
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
  <div className="depth-chart">
    <h2>Order Book</h2>
    <table>
      <thead>
        <tr>
          <th>Bids</th>
        </tr>
      </thead>
      <tbody>
        {bids.map((entry, index) => (
          <tr key={index}>
            <td>{JSON.stringify(entry)}</td>
          </tr>
        ))}
      </tbody>
    </table>

    <table>
      <thead>
        <tr>
          <th>Asks</th>
        </tr>
      </thead>
      <tbody>
        {asks.map((entry, index) => (
          <tr key={index}>
            <td>{JSON.stringify(entry)}</td>
          </tr>
        ))}
      </tbody>
    </table>
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