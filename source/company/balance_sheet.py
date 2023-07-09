import random
import json

def generate_fake_balance_sheet(date, symbol, period):
    balance_sheet = {
        "date": date,
        "symbol": symbol,
        "reportedCurrency": "USD",
        "calendarYear": date[:4],
        "period": period,
    }

    cash_and_cash_equivalents = random.randint(1000000000, 30000000000)
    short_term_investments = random.randint(1000000000, 30000000000)
    cash_and_short_term_investments = cash_and_cash_equivalents + short_term_investments
    net_receivables = random.randint(10000000000, 40000000000)
    inventory = random.randint(1000000000, 10000000000)
    other_current_assets = random.randint(1000000000, 20000000000)
    total_current_assets = cash_and_short_term_investments + net_receivables + inventory + other_current_assets

    property_plant_equipment_net = random.randint(10000000000, 50000000000)
    goodwill = random.randint(0, 10000000000)
    intangible_assets = random.randint(0, 10000000000)
    goodwill_and_intangible_assets = goodwill + intangible_assets
    long_term_investments = random.randint(10000000000, 200000000000)
    tax_assets = random.randint(0, 10000000000)
    other_non_current_assets = random.randint(10000000000, 80000000000)
    total_non_current_assets = property_plant_equipment_net + goodwill_and_intangible_assets + long_term_investments + tax_assets + other_non_current_assets

    other_assets = random.randint(0, 10000000000)
    total_assets = total_current_assets + total_non_current_assets + other_assets

    account_payables = random.randint(10000000000, 50000000000)
    short_term_debt = random.randint(1000000000, 20000000000)
    tax_payables = random.randint(0, 10000000000)
    deferred_revenue = random.randint(1000000000, 20000000000)
    other_current_liabilities = random.randint(10000000000, 60000000000)
    total_current_liabilities = account_payables + short_term_debt + tax_payables + deferred_revenue + other_current_liabilities

    long_term_debt = random.randint(50000000000, 150000000000)
    deferred_revenue_non_current = random.randint(0, 10000000000)
    deferred_tax_liabilities_non_current = random.randint(0, 10000000000)
    other_non_current_liabilities = random.randint(10000000000, 60000000000)
    total_non_current_liabilities = long_term_debt + deferred_revenue_non_current + deferred_tax_liabilities_non_current + other_non_current_liabilities

    other_liabilities = random.randint(0, 10000000000)
    capital_lease_obligations = random.randint(0, 10000000000)
    total_liabilities = total_current_liabilities + total_non_current_liabilities + other_liabilities + capital_lease_obligations

    preferred_stock = random.randint(0, 10000000000)
    common_stock = random.randint(5000000000, 80000000000)
    retained_earnings = lambda x = 0: x if (random.randint(0,2) != 2) else random.randint(0, 10000000000)
    accumulated_other_comprehensive_income_loss = random.randint(-20000000000, 0)
    other_total_stockholders_equity = random.randint(0, 10000000000)
    total_stockholders_equity = common_stock + retained_earnings + accumulated_other_comprehensive_income_loss + other_total_stockholders_equity

    total_equity = total_stockholders_equity
    total_liabilities_and_stockholders_equity = total_liabilities + total_equity

    minority_interest = random.randint(0, 10000000000)
    total_liabilities_and_total_equity = total_liabilities_and_stockholders_equity + minority_interest

    total_investments = short_term_investments
    total_debt = short_term_debt + long_term_debt
    net_debt = total_debt - cash_and_cash_equivalents

    balance_sheet["cashAndCashEquivalents"] = cash_and_cash_equivalents
    balance_sheet["shortTermInvestments"] = short_term_investments
    balance_sheet["cashAndShortTermInvestments"] = cash_and_short_term_investments
    balance_sheet["netReceivables"] = net_receivables
    balance_sheet["inventory"] = inventory
    balance_sheet["otherCurrentAssets"] = other_current_assets
    balance_sheet["totalCurrentAssets"] = total_current_assets
    balance_sheet["propertyPlantEquipmentNet"] = property_plant_equipment_net
    balance_sheet["goodwill"] = goodwill
    balance_sheet["intangibleAssets"] = intangible_assets
    balance_sheet["goodwillAndIntangibleAssets"] = goodwill_and_intangible_assets
    balance_sheet["longTermInvestments"] = long_term_investments
    balance_sheet["taxAssets"] = tax_assets
    balance_sheet["otherNonCurrentAssets"] = other_non_current_assets
    balance_sheet["totalNonCurrentAssets"] = total_non_current_assets
    balance_sheet["otherAssets"] = other_assets
    balance_sheet["totalAssets"] = total_assets
    balance_sheet["accountPayables"] = account_payables
    balance_sheet["shortTermDebt"] = short_term_debt
    balance_sheet["taxPayables"] = tax_payables
    balance_sheet["deferredRevenue"] = deferred_revenue
    balance_sheet["otherCurrentLiabilities"] = other_current_liabilities
    balance_sheet["totalCurrentLiabilities"] = total_current_liabilities
    balance_sheet["longTermDebt"] = long_term_debt
    balance_sheet["deferredRevenueNonCurrent"] = deferred_revenue_non_current
    balance_sheet["deferredTaxLiabilitiesNonCurrent"] = deferred_tax_liabilities_non_current
    balance_sheet["otherNonCurrentLiabilities"] = other_non_current_liabilities
    balance_sheet["totalNonCurrentLiabilities"] = total_non_current_liabilities
    balance_sheet["otherLiabilities"] = other_liabilities
    balance_sheet["capitalLeaseObligations"] = capital_lease_obligations
    balance_sheet["totalLiabilities"] = total_liabilities
    balance_sheet["preferredStock"] = preferred_stock
    balance_sheet["commonStock"] = common_stock
    balance_sheet["retainedEarnings"] = retained_earnings
    balance_sheet["accumulatedOtherComprehensiveIncomeLoss"] = accumulated_other_comprehensive_income_loss
    balance_sheet["othertotalStockholdersEquity"] = other_total_stockholders_equity
    balance_sheet["totalStockholdersEquity"] = total_stockholders_equity
    balance_sheet["totalEquity"] = total_equity
    balance_sheet["totalLiabilitiesAndStockholdersEquity"] = total_liabilities_and_stockholders_equity
    balance_sheet["minorityInterest"] = minority_interest
    balance_sheet["totalLiabilitiesAndTotalEquity"] = total_liabilities_and_total_equity
    balance_sheet["totalInvestments"] = total_investments
    balance_sheet["totalDebt"] = total_debt
    balance_sheet["netDebt"] = net_debt

    return balance_sheet

# Example usage
fake_balance_sheet = generate_fake_balance_sheet()
print(fake_balance_sheet)
