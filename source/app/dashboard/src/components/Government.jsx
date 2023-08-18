import React, { useState, useEffect } from 'react'

const Government = () => {
  const [taxData, setTaxData] = useState([])
  const [cashData, setCashData] = useState([])

  useEffect(() => {
    // Fetch tax data
    fetch('http://localhost:5001/api/v1/get_last_collected_taxes')
      .then(response => response.json())
      .then(data => setTaxData(data))
      .catch(error => console.error('Error fetching tax data:', error))

    // Fetch cash data
    fetch('http://localhost:5001/api/v1/get_cash')
      .then(response => response.json())
      .then(data => setCashData(data))
      .catch(error => console.error('Error fetching cash data:', error))
  }, [])

  return (
    <div style={{ display: 'flex' }}>
      <div style={{ flex: 1, marginRight: '20px' }}>
        <h2>Last Collected Taxes</h2>
        <ul>
          {taxData}
        </ul>
      </div>
      <div style={{ flex: 1 }}>
        <h2>Cash Data</h2>
        <ul>
          {cashData}
        </ul>
      </div>
    </div>
  )
}

export default Government