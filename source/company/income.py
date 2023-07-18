import random
import json

def generate_fake_income_statement(date, symbol, period):
    income_statement = {
        "date": date,
        "symbol": symbol,
        "reportedCurrency": "USD",
        "calendarYear": date[:4],
        "period": period,
    }

    revenue = random.randint(5000000000, 100000000000)
    cost_of_revenue = random.randint(1000000000, 60000000000)
    gross_profit = revenue - cost_of_revenue
    gross_profit_ratio = round(gross_profit / revenue, 10)

    research_and_development_expenses = random.randint(0, 10000000000)
    general_and_administrative_expenses = random.randint(0, 10000000000)
    selling_and_marketing_expenses = random.randint(0, 10000000000)
    selling_general_and_administrative_expenses = random.randint(0, 10000000000)
    other_expenses = random.randint(0, 10000000000)
    operating_expenses = research_and_development_expenses + general_and_administrative_expenses + selling_and_marketing_expenses + selling_general_and_administrative_expenses + other_expenses
    cost_and_expenses = cost_of_revenue + operating_expenses

    interest_income = random.randint(0, 2000000000)
    interest_expense = random.randint(0, 2000000000)
    depreciation_and_amortization = random.randint(0, 5000000000)
    ebitda = gross_profit - operating_expenses + interest_income - interest_expense + depreciation_and_amortization
    ebitda_ratio = round(ebitda / revenue, 10)

    operating_income = ebitda - interest_income + interest_expense
    operating_income_ratio = round(operating_income / revenue, 10)

    total_other_income_expenses_net = random.randint(-100000000, 100000000)
    income_before_tax = operating_income + total_other_income_expenses_net
    income_before_tax_ratio = round(income_before_tax / revenue, 10)

    income_tax_expense = random.randint(0, 5000000000)
    net_income = income_before_tax - income_tax_expense
    net_income_ratio = round(net_income / revenue, 10)

    eps = round(net_income / random.randint(10000000000, 20000000000), 2)
    eps_diluted = round(net_income / random.randint(10000000000, 20000000000), 2)

    weighted_average_shs_out = random.randint(1000000000, 20000000000)
    weighted_average_shs_out_dil = random.randint(1000000000, 20000000000)

    income_statement["revenue"] = revenue
    income_statement["costOfRevenue"] = cost_of_revenue
    income_statement["grossProfit"] = gross_profit
    income_statement["grossProfitRatio"] = gross_profit_ratio
    income_statement["researchAndDevelopmentExpenses"] = research_and_development_expenses
    income_statement["generalAndAdministrativeExpenses"] = general_and_administrative_expenses
    income_statement["sellingAndMarketingExpenses"] = selling_and_marketing_expenses
    income_statement["sellingGeneralAndAdministrativeExpenses"] = selling_general_and_administrative_expenses
    income_statement["otherExpenses"] = other_expenses
    income_statement["operatingExpenses"] = operating_expenses
    income_statement["costAndExpenses"] = cost_and_expenses
    income_statement["interestIncome"] = interest_income
    income_statement["interestExpense"] = interest_expense
    income_statement["depreciationAndAmortization"] = depreciation_and_amortization
    income_statement["ebitda"] = ebitda
    income_statement["ebitdaratio"] = ebitda_ratio
    income_statement["operatingIncome"] = operating_income
    income_statement["operatingIncomeRatio"] = operating_income_ratio
    income_statement["totalOtherIncomeExpensesNet"] = total_other_income_expenses_net
    income_statement["incomeBeforeTax"] = income_before_tax
    income_statement["incomeBeforeTaxRatio"] = income_before_tax_ratio
    income_statement["incomeTaxExpense"] = income_tax_expense
    income_statement["netIncome"] = net_income
    income_statement["netIncomeRatio"] = net_income_ratio
    income_statement["eps"] = eps
    income_statement["epsdiluted"] = eps_diluted
    income_statement["weightedAverageShsOut"] = weighted_average_shs_out
    income_statement["weightedAverageShsOutDil"] = weighted_average_shs_out_dil
    income_statement["link"] = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000064/0000320193-23-000064-index.htm"
    income_statement["finalLink"] = "https://www.sec.gov/Archives/edgar/data/320193/000032019323000064/aapl-20230401.htm"

    return income_statement
