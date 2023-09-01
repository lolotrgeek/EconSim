import React from 'react'
import { Link } from 'react-router-dom'
import '../styles/Tickers.css'

const Tickers = ({ tickers, selectedTicker }) => {
  return (
    <div className="ticker-grid">
      <div className="ticker-list">
        {tickers.map((ticker, index) => (
          <Link key={index} to={`/exchange/${encodeURIComponent(ticker)}`}>
          <div
            key={index}
            className={`ticker ${selectedTicker === ticker ? 'selected' : ''}`}
          >
            {ticker}
          </div>
          </Link>
        ))}
      </div>
    </div>
  )
}

export default Tickers