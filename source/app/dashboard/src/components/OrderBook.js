import React from 'react';
import '../styles/OrderBook.css';

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

export default OrderBook;