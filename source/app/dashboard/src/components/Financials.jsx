import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const fetcher = async (query, tries = 0, maxTries = 5) => {
  try {
    return await query()
  } catch (error) {
    if (tries < maxTries) {
      return await fetcher(query, tries + 1, maxTries)
    }
    return { "error": "Could not parse query" }
  }
}

const parser = data => {
  try {
    return JSON.parse(data)
  } catch (error) {
    return { "error": "Could not parse data" }
  }
}
function Financials() {
  const location = useLocation()
  let company = location.pathname.replace('/exchange/', '')
  const [activeTab, setActiveTab] = useState('income')
  const [incomeStatement, setIncomeStatement] = useState(null)
  const [balanceSheet, setBalanceSheet] = useState(null)
  const [cashFlow, setCashFlow] = useState(null)

  const url = 'http://localhost:5002/api/v1/'

  useEffect(() => {
    const fetchData = async () => {
      if (!company || company === '' || company === 'undefined') return
      try {
        if (activeTab === 'income') {
          setIncomeStatement({})
          fetcher(async () => {
            const response = await fetch(url + 'get_income_statement?company=' + company)
            const data = await response.json()
            const parsedData = parser(data)
            setIncomeStatement(parsedData)
          })
        }
        if (activeTab === 'balance') {
          setBalanceSheet({})
          fetcher(async () => {
            const response = await fetch(url + 'get_balance_sheet?company=' + company)
            const data = await response.json()

            const parsedData = parser(data)
            setBalanceSheet(parsedData)
          })
        }
        if (activeTab === 'cash') {
          setCashFlow({})
          fetcher(async () => {
            const response = await fetch(url + 'get_cash_flow?company=' + company)
            const data = await response.json()

            const parsedData = parser(data)
            setCashFlow(parsedData)
          })
        }
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }
    fetchData()
  }, [activeTab, company])

  const handleTabChange = (tab) => {
    setActiveTab(tab)
  }

  const renderTabContent = () => {
    switch (activeTab) {
      case 'income':
        return (
          <pre className="data-box">
            {incomeStatement ? Object.entries(incomeStatement).map(([key, value]) => (
              <div key={key}>
                {key}: {value}
              </div>
            )) : null
            }
          </pre>
        )
      case 'balance':
        return (
          <pre className="data-box">
            {balanceSheet ? Object.entries(balanceSheet).map(([key, value]) => (
              <div key={key}>
                {key}: {value}
              </div>
            )) : null
            }

          </pre>
        )
      case 'cash':
        return (
          <pre className="data-box">
            {cashFlow ? Object.entries(cashFlow).map(([key, value]) => (
              <div key={key}>
                {key}: {value}
              </div>
            )) : null
            }
          </pre>
        )
      default:
        return null
    }
  }

  return (
    <div> 
      {company}
      <div className="tab-container">
        <button
          className={activeTab === 'income' ? 'active-tab' : 'tab'}
          onClick={() => handleTabChange('income')}
        >
          Income Statement
        </button>
        <button
          className={activeTab === 'balance' ? 'active-tab' : 'tab'}
          onClick={() => handleTabChange('balance')}
        >
          Balance Sheet
        </button>
        <button
          className={activeTab === 'cash' ? 'active-tab' : 'tab'}
          onClick={() => handleTabChange('cash')}
        >
          Cash Flow
        </button>
      </div>
      <div className="tab-content">
        {renderTabContent()}
      </div>
    </div>
  )
}

export default Financials
