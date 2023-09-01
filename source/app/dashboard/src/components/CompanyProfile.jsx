import React, { useState, useEffect } from 'react'
import { useLocation } from 'react-router-dom'

const fetcher = async (query, tries = 0, maxTries = 3) => {
    try {
        return await query()
    } catch (error) {
        if (tries < maxTries) {
            return await fetcher(query, tries + 1, maxTries)
        }
        return { "error": "Could not parse query" }
    }
}

function CompanyData() {
    const location = useLocation()
    let company = location.pathname.replace('/exchange/', '')
    const [companyData, setCompanyData] = useState({})
    const url = 'http://localhost:5002/api/v1/'

    const fetchData = async () => {
        try {
            if (!company || company === '' || company === 'undefined') return
            fetcher(async () => {
                const response = await fetch(url + 'get_company?company=' + company)
                const data = await response.json()
                const parsedData = JSON.parse(data)
                setCompanyData(parsedData)
            })
        } catch (error) {
            console.error('Error fetching data:', error)
        }
    }

    useEffect(() => {
        fetchData()
    }, [company])

    return (
        <div>
            <pre className="data-box">
                {companyData ? Object.entries(companyData).map(([key, value]) => (
                    <div key={key}>
                        {key}: {JSON.stringify(value)}
                    </div>
                )) : null
                }
            </pre>
        </div>
    )
}

export default CompanyData
