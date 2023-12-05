import React, { useState, useEffect } from 'react'
import { parse } from '../utils'

const Government = () => {
  const [taxData, setTaxData] = useState([])
  const [cashData, setCashData] = useState([])
  const [backTaxes, setBackTaxes] = useState([])

  useEffect(() => {
    const fetchData = async () => {
      try {
        const taxResponse = await fetch('http://localhost:5580/api/v1/get_taxes_collected')
        const taxDataJson = await taxResponse.json()
        const parsedTaxData = parse(taxDataJson)
        // reduce the parsed data to accumulate the total of short-term and long-term taxes collected
        const reducedTaxData = parsedTaxData.reduce((acc, cur) => {
          acc.long_term += cur.long_term
          acc.short_term += cur.short_term
          return acc
        }, { long_term: 0, short_term: 0 })
        reducedTaxData.year = parsedTaxData[0].tax_year
        setTaxData(reducedTaxData)

        const cashResponse = await fetch('http://localhost:5580/api/v1/get_cash')
        const cashData = await cashResponse.json()
        const new_cash_data = parse(cashData)
        setCashData(new_cash_data)

        const backTaxesResponse = await fetch('http://localhost:5580/api/v1/get_back_taxes')
        const backTaxesData = await backTaxesResponse.json()
        const new_back_taxes = parse(backTaxesData)
        setBackTaxes(new_back_taxes)
      } catch (error) {
        console.error('Error fetching data:', error)
      }
    }

    const interval = setInterval(() => {
      fetchData()
    }, 1000)

    return () => clearInterval(interval)
  }, [])

  return (
    <div style={{ display: 'flex' }}>
      <div style={{ flex: 1, marginRight: '20px' }}>
        <div style={{ flex: 1 }}>
          <h2>Cash Data</h2>
          <ul>
            {cashData}
          </ul>
        </div>
        <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
          <div style={{ flex: 1, display: 'flex', flexDirection: 'column' }}>
            <h2>Tax Records</h2>
            {taxData?
              <div>
                <div>Year: {taxData.year}</div>
                <div>Long-term: {taxData.long_term}</div>
                <div>Short-term: {taxData.short_term}</div>
              </div>
              : <div>No tax records</div>}
          </div>
          <div style={{ display: 'flex' }}>
            <h2>Back Taxes</h2>
            <ul>
              {backTaxes}
            </ul>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Government