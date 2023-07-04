import json
import random

def generate_fake_cash_flow(retained_earnings, date, symbol, period):
    cash_flow = {
        "date": date,
        "symbol": symbol,
        "reportedCurrency": "USD",
        "calendarYear": date[:4],
        "period": period,
        "netIncome": random.randint(20000000000, 30000000000),
        "depreciationAndAmortization": random.randint(1000000000, 4000000000),
        "deferredIncomeTax": 0,
        "stockBasedCompensation": random.randint(2000000000, 3000000000),
        "changeInWorkingCapital": random.randint(-500000000, 500000000),
        "accountsReceivables": random.randint(5000000000, 6000000000),
        "inventory": random.randint(-1000000000, -500000000),
        "accountsPayables": random.randint(-15000000000, -10000000000),
        "otherWorkingCapital": random.randint(10000000000, 15000000000),
        "otherNonCashItems": random.randint(-2000000000, -1000000000),
        "netCashProvidedByOperatingActivities": random.randint(20000000000, 30000000000),
        "investmentsInPropertyPlantAndEquipment": random.randint(-3000000000, -2000000000),
        "acquisitionsNet": 0,
        "purchasesOfInvestments": random.randint(-7000000000, -6000000000),
        "salesMaturitiesOfInvestments": random.randint(10000000000, 12000000000),
        "otherInvestingActivites": random.randint(-200000000, 200000000),
        "netCashUsedForInvestingActivites": random.randint(1000000000, 3000000000),
        "debtRepayment": random.randint(-7000000000, -5000000000),
        "commonStockIssued": 0,
        "commonStockRepurchased": random.randint(-20000000000, -18000000000),
        "dividendsPaid": random.random() * retained_earnings * -1,
        "otherFinancingActivites": random.randint(3000000000, 4000000000),
        "netCashUsedProvidedByFinancingActivities": random.randint(-27000000000, -25000000000),
        "effectOfForexChangesOnCash": 0,
        "netChangeInCash": random.randint(500000000, 6000000000),
        "cashAtEndOfPeriod": random.randint(25000000000, 30000000000),
        "cashAtBeginningOfPeriod": random.randint(20000000000, 24000000000),
        "operatingCashFlow": random.randint(20000000000, 30000000000),
        "capitalExpenditure": random.randint(-3000000000, -2000000000),
        "freeCashFlow": random.randint(20000000000, 26000000000),
    }
    return cash_flow

# Example usage
fake_cash_flow = generate_fake_cash_flow()
print(fake_cash_flow)
