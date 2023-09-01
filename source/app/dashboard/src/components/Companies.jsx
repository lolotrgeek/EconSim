import React, { useState, useEffect } from 'react'

const Companies = () => {
    const [incomeStatement, setIncomeStatement] = useState(null)
    const [balanceSheet, setBalanceSheet] = useState(null)
    const [cashFlow, setCashFlow] = useState(null)


  const url = 'http://localhost:5002/api/v1/'

  useEffect(() => {
    fetch(url+'get_income_statement')
      .then(response => response.json())
      .then(data => setIncomeStatement(data))
      .catch(error => console.error('Error fetching income data:', error))

    fetch(url+'get_balance_sheet')
        .then(response => response.json())
        .then(data => setBalanceSheet(data))
        .catch(error => console.error('Error fetching balance data:', error))

    fetch(url+'get_cash_flow')
        .then(response => response.json())
        .then(data => setCashFlow(data))
        .catch(error => console.error('Error fetching cash flow data:', error))

    

  }, [])

  return (
    <div style={{ display: 'flex' }}>
        <div style={{ flex: 1 }}>
            <h2>Companies</h2>
            <ul>
            {companies.map((company, index) => (
                <li key={index}>
                {company}
                </li>
            ))}
            </ul>
        </div>

    </div>
  )
}

export default Companies