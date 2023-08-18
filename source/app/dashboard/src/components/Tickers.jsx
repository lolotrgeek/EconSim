import React from 'react'
import '../styles/Tickers.css'

const Tickers = ({ tickers, selectedTicker, onTickerSelect }) => {
  return (
    <div className="ticker-grid">
      <div className="ticker-list">
        {tickers.map((ticker, index) => (
          <div
            key={index}
            className={`ticker ${selectedTicker === ticker ? 'selected' : ''}`}
            onClick={() => onTickerSelect(ticker)}
          >
            {ticker}
          </div>
        ))}
      </div>
    </div>
  )
}

export default Tickers