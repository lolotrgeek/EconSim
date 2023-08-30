import random

#TODO: ensure that if revenue is less than the expenses that debt and/or financing is increased to cover the difference

class Operations():
    def __init__(self, market_cap, tax_rate=0.15):
        self.market_cap = market_cap
        #Revenue
        self.revenue = self.generate_by_market_cap()
        self.deferred_revenue = self.revenue * random.uniform(0.1, 0.2)
        self.deferred_revenue_non_current = self.revenue * random.uniform(0.1, 0.2)
        self.net_receivables = self.revenue * random.uniform(0.1, 0.2)
        self.account_receivable = 0
        #Expenses
        self.expenses = self.generate_by_market_cap()
        self.cost_of_revenue = 0
        self.research_and_development_expenses = 0
        self.general_and_administrative_expenses = 0
        self.selling_and_marketing_expenses = 0
        self.selling_general_and_administrative_expenses = 0
        self.other_expenses = 0
        self.total_other_income_expenses_net = 0
        self.accounts_payable = 0
        self.accounts_payable_balance = 0
        # Debt
        self.debt = self.generate_by_market_cap()
        self.short_term_debt = self.debt * random.uniform(0.1, 0.5)
        self.long_term_debt = self.debt - self.short_term_debt
        self.interest_rate = random.uniform(0.001, 0.1)
        self.debtRepayment = 0
        self.interest_expense = 0
        self.total_debt = 0
        # Tax
        self.tax_rate = tax_rate
        self.taxAssets = 0
        self.income_tax_expense = 0
        self.deferred_income_tax = 0
        self.deferredTaxLiabilitiesNonCurrent = 0
        self.taxPayables = 0
        # Capital
        self.capital = self.generate_by_market_cap()
        self.inventory = 0
        self.investments_in_ppe = 0
        self.ppe_net = 0
        self.depreciation_and_amortization_current = 0
        self.depreciation_and_amortization = 0
        self.capitalLeaseObligations = 0
        self.otherWorkingCapital = 0
        self.inventory_balance = 0 
        self.capital_expenditures = 0                     
        # Investment
        self.investments = self.generate_by_market_cap()
        self.purchases_of_investments = 0
        self.acquisitions_net = 0
        self.other_investing_activites = 0
        self.short_term_investments = 0
        self.long_term_investments = 0
        self.goodwill = 0
        self.otherNonCurrentAssets = 0
        self.sales_maturities_of_investments = 0
        self.total_investments = 0
        self.minority_interest = 0
        # Equity
        self.equity = self.generate_by_market_cap()
        self.stock_based_compensation = 0
        self.preferred_stock = 0
        self.common_stock = 0
        self.common_stock_repurchased = 0
        self.common_stock_issued = 0
        self.accumulated_other_comprehensive_income_loss = 0
        self.other_stockholder_equity = 0
        # NonCash
        self.other_non_cash_items = 0
        self.other_current_assets = 0
        self.intangible_assets = 0
        self.other_assets = 0        
        # Cash
        self.net_income = 0
        self.retained_earnings = 0
        self.dividends_paid = 0
        self.cash_and_cash_equivalents = 0
        self.interest_income = 0
        self.cash_at_beginning_of_period = 0
        self.cash_at_end_of_period = 0     
        #Financing
        self.other_financing_activites = 0
        self.other_liabilities = 0
        self.other_current_liabilities = 0
        self.other_non_current_liabilities = 0
        # Income
        self.gross_profit = 0
        self.gross_profit_ratio = 0
        self.operating_expenses = 0
        self.cost_and_expenses = 0
        self.ebitda = 0
        self.ebitda_ratio = 0
        self.operating_income = 0
        self.operating_income_ratio = 0
        self.income_before_tax = 0
        self.income_before_tax_ratio = 0
        self.net_income = 0
        self.net_income_ratio = 0
        self.weighted_average_shs_out = 0
        self.weighted_average_shs_out_dil = 0
        self.eps = 0
        self.eps_diluted = 0

    def generate_by_market_cap(self):
        if self.market_cap == 'large': return random.randint(1_000_000_000, 1_000_000_000_000)
        elif self.market_cap == 'medium': return random.randint(100_000_000, 1_000_000_000)
        elif self.market_cap == 'small': return random.randint(1_000_000, 100_000_000)
        else: return random.randint(1_000, 1_000_000)        

    def nextRevenue(self):
        payments_received = self.net_receivables * random.uniform(0.01, 0.2)
        self.net_receivables -= payments_received
        next_revenue = self.revenue * random.uniform(0.9, 1.1) 
        
        # how much of revenue is deferred
        self.deferred_revenue += next_revenue * random.uniform(-0.2, 0.2)
        self.deferred_revenue_non_current += next_revenue * random.uniform(-0.2, 0.2)

        # generate the receivables for this period
        self.account_receivable = next_revenue * random.uniform(0.0, 0.1) # the receviables for this period
        self.net_receivables += self.account_receivable # the remaining receivables from this and all prior periods
        
        self.revenue = next_revenue        

    def nextExpenses(self):
        next_expenses = self.expenses * random.uniform(0.9, 1.1)

        # pay down old payables
        if self.accounts_payable_balance > 0:
            pay_down_accounts = self.accounts_payable_balance * random.uniform(0.01, 0.1)
            next_expenses += pay_down_accounts #NOTE: normally this would increase cost of revenue, but this reduces complexity
            self.accounts_payable_balance -= pay_down_accounts

        self.cost_of_revenue = next_expenses * random.uniform(0.3, 0.5)
        self.research_and_development_expenses = next_expenses * random.uniform(0.01, 0.1)
        self.general_and_administrative_expenses = next_expenses * random.uniform(0.01, 0.1)
        self.selling_and_marketing_expenses = next_expenses * random.uniform(0.01, 0.1)
        self.selling_general_and_administrative_expenses = next_expenses * random.uniform(0.01, 0.1)
        self.other_expenses = next_expenses * random.uniform(0.01, 0.1)
        self.total_other_income_expenses_net = next_expenses - (self.cost_of_revenue + self.research_and_development_expenses + self.general_and_administrative_expenses + self.selling_and_marketing_expenses + self.selling_general_and_administrative_expenses + self.other_expenses)        
        
        # generate the payables for this period
        self.accounts_payable = self.cost_of_revenue * random.uniform(0.1, 0.2)
        self.accounts_payable_balance += self.accounts_payable

        self.expenses = next_expenses        

    def nextDebt(self):
        short_term_debt_interest = self.interest_rate * self.short_term_debt
        long_term_debt_interest = self.interest_rate * self.long_term_debt
        self.interest_expense = short_term_debt_interest + long_term_debt_interest
        self.debtRepayment = self.debt * random.uniform(0.01, 0.2)

        short_term_debt_repayment = self.debtRepayment * random.uniform(0.5, 0.8)
        long_term_debt_repayment = self.debtRepayment - short_term_debt_repayment

        # pay down old debt
        self.short_term_debt -= short_term_debt_repayment
        self.long_term_debt -= long_term_debt_repayment
        
        # generate new debt
        more_debt = random.randint(0, 1)
        if more_debt == 1:
            self.short_term_debt += self.debt * random.uniform(0.0, 0.1)
            self.long_term_debt += self.debt * random.uniform(0.0, 0.1)

        self.total_debt += self.short_term_debt + self.long_term_debt

        self.debt = self.short_term_debt + self.long_term_debt

    def nextTax(self):
        """
        depends on income_before_tax
        """
        # calculate taxes
        self.taxPayables = self.income_before_tax * self.tax_rate

        # use any pre-paid taxes
        if self.taxAssets > 0:
            self.income_tax_expense -= self.taxAssets
            self.taxAssets = 0
        # pay taxes
        self.income_tax_expense = self.taxPayables * random.uniform(0.0, 1)

        # defer taxes
        self.deferred_income_tax = self.taxPayables - self.income_tax_expense
        self.deferredTaxLiabilitiesNonCurrent += self.deferred_income_tax

        # prepay taxes
        self.taxAssets = self.income_tax_expense * random.uniform(0.0, 0.1)

    def nextCapital(self):
        """
        depends on cost of_revenue
        """
        self.inventory = self.capital * random.uniform(0.1, 0.2)
        self.inventory_balance += self.inventory

        previous_investments_in_ppe = self.investments_in_ppe
        self.investments_in_ppe = self.capital * random.uniform(0.1, 0.2)
        self.capital_expenditures = self.investments_in_ppe - previous_investments_in_ppe + self.depreciation_and_amortization_current
        self.ppe_net += self.investments_in_ppe

        self.depreciation_and_amortization_current = self.investments_in_ppe * random.uniform(0.01, 0.1)
        self.depreciation_and_amortization = self.ppe_net * random.uniform(0.01, 0.1)

        self.otherWorkingCapital = self.capital * random.uniform(0.1, 0.2)
        self.capitalLeaseObligations = self.cost_of_revenue * random.uniform(0.3, 0.5)

    def nextInvestment(self):
        """
        depends on cash_and_cash_equivalents
        """
        # sell off some investments
        if self.investments > 0:
            self.sales_maturities_of_investments = self.investments * random.uniform(0.01, 0.2)
            self.investments -= self.sales_maturities_of_investments
        
        # use cash to buy more investments
        cash_to_invest = self.cash_and_cash_equivalents * random.uniform(0.01, 0.2)
        self.cash_and_cash_equivalents -= cash_to_invest
        next_investments = cash_to_invest
        
        # buy more investments
        self.purchases_of_investments = next_investments * random.uniform(0.01, 0.2)
        self.acquisitions_net = next_investments * random.uniform(0.01, 0.2)
        self.other_investing_activites = next_investments * random.uniform(0.01, 0.2)

        self.short_term_investments = self.purchases_of_investments * random.uniform(0.1, 0.8)
        self.long_term_investments = self.purchases_of_investments - self.short_term_investments + self.acquisitions_net

        self.goodwill = self.acquisitions_net * random.uniform(0.1, 0.2)

        self.otherNonCurrentAssets = self.other_investing_activites * random.uniform(0.1, 0.2)

        self.total_investments += self.short_term_investments + self.long_term_investments + self.goodwill + self.otherNonCurrentAssets

        self.investments = next_investments

    def nextEquity(self, shares_issued, shares_repurchased ):
        next_equity = self.equity * random.uniform(0.9, 1.1)

        compensate_with_stock = random.randint(0, 5)
        if compensate_with_stock == 5:
            self.stock_based_compensation = next_equity * random.uniform(0.01, 0.1)
        
        issue_preferred_stock = random.randint(0, 5)
        if issue_preferred_stock == 5:
            self.preferred_stock = next_equity * random.uniform(0.01, 0.1)

        self.common_stock_issued = shares_issued 
        self.common_stock_repurchased = shares_repurchased
        self.common_stock += shares_issued
        self.common_stock -= shares_repurchased

        if self.common_stock < 0:
            self.accumulated_other_comprehensive_income_loss += self.common_stock_issued - self.common_stock_repurchased
        else:
            self.accumulated_other_comprehensive_income_loss = 0

        self.other_stockholder_equity = next_equity * random.uniform(0.01, 0.1)

    def nextNonCash(self):
        """
        depends on revenue, expenses, investments
        """
        #TODO: these need to balance...
        self.other_current_assets = self.revenue * random.uniform(0.01, 0.1)
        self.intangible_assets = self.expenses * random.uniform(0.01, 0.1)
        self.other_assets = self.investments * random.uniform(0.01, 0.1)

        self.other_non_cash_items = self.other_current_assets + self.intangible_assets + self.other_assets

    def nextCash(self):
        self.cash_at_beginning_of_period = self.cash_at_end_of_period
        self.net_income = self.revenue - self.expenses - self.interest_expense + self.interest_income - self.income_tax_expense 
        self.retained_earnings += self.net_income
        self.dividends_paid = self.retained_earnings * random.uniform(0.01, 0.8)
        self.retained_earnings -= self.dividends_paid
        self.cash_and_cash_equivalents += self.net_income - self.dividends_paid
        self.interest_income = self.cash_and_cash_equivalents * random.uniform(0.01, 0.1)
        self.cash_at_end_of_period = self.cash_and_cash_equivalents

    def nextFinancing(self):
        """
        depends on investments, equity
        """
        #TODO: these need to balance...
        self.other_liabilities = self.investments * random.uniform(0.01, 0.1)
        self.other_current_liabilities = self.equity * random.uniform(0.01, 0.1)
        self.other_non_current_liabilities = self.equity * random.uniform(0.01, 0.1)
        self.other_financing_activites = self.other_liabilities + self.other_current_liabilities + self.other_non_current_liabilities

    def nextIncome(self, outstanding_shares, shares_issued):
        self.gross_profit = self.revenue - self.cost_of_revenue
        self.gross_profit_ratio = round(self.gross_profit / self.revenue, 10)
        self.operating_expenses = self.research_and_development_expenses + self.general_and_administrative_expenses + self.selling_and_marketing_expenses + self.selling_general_and_administrative_expenses + self.other_expenses
        self.cost_and_expenses = self.cost_of_revenue + self.operating_expenses
        self.ebitda = self.gross_profit - self.operating_expenses + self.interest_income - self.interest_expense + self.depreciation_and_amortization_current
        self.ebitda_ratio = round(self.ebitda / self.revenue, 10)
        self.operating_income = self.ebitda - self.interest_income + self.interest_expense
        self.operating_income_ratio = round(self.operating_income / self.revenue, 10)
        self.income_before_tax = self.operating_income + self.total_other_income_expenses_net
        self.income_before_tax_ratio = round(self.income_before_tax / self.revenue, 10)
        self.net_income = self.income_before_tax - self.income_tax_expense
        self.net_income_ratio = round(self.net_income / self.revenue, 10)
        self.weighted_average_shs_out = outstanding_shares / 1
        self.weighted_average_shs_out_dil = shares_issued / 1
        if weighted_average_shs_out_dil == 0: weighted_average_shs_out_dil = 1 # NOTE: outstanding shares cannot be 0
        self.eps = round(self.net_income / self.weighted_average_shs_out, 2)
        self.eps_diluted = round(self.net_income / self.weighted_average_shs_out_dil, 2)             

    def next(self, outstanding_shares, shares_issued, shares_repurchased):
        self.nextRevenue()
        self.nextExpenses()
        self.nextDebt()
        self.nextCapital()
        self.nextEquity(shares_issued, shares_repurchased)
        self.nextCash()
        self.nextInvestment()
        self.nextFinancing()
        self.nextNonCash()
        self.nextIncome(outstanding_shares, shares_issued)
        self.nextTax()

    def generate_income_statement(self, date, symbol, period) -> dict:
        income_statement = {
            "date": date,
            "symbol": symbol,
            "reportedCurrency": "USD",
            "calendarYear": date.year,
            "period": period,
        }

        income_statement["revenue"] = self.revenue
        income_statement["costOfRevenue"] = self.cost_of_revenue
        income_statement["grossProfit"] = self.gross_profit
        income_statement["grossProfitRatio"] = self.gross_profit_ratio
        income_statement["researchAndDevelopmentExpenses"] = self.research_and_development_expenses
        income_statement["generalAndAdministrativeExpenses"] = self.general_and_administrative_expenses
        income_statement["sellingAndMarketingExpenses"] = self.selling_and_marketing_expenses
        income_statement["sellingGeneralAndAdministrativeExpenses"] = self.selling_general_and_administrative_expenses
        income_statement["otherExpenses"] = self.other_expenses
        income_statement["operatingExpenses"] = self.operating_expenses
        income_statement["costAndExpenses"] = self.cost_and_expenses
        income_statement["interest_income"] = self.interest_income
        income_statement["interest_expense"] = self.interest_expense
        income_statement["depreciationAndAmortization"] = self.depreciation_and_amortization_current
        income_statement["ebitda"] = self.ebitda
        income_statement["ebitdaratio"] = self.ebitda_ratio
        income_statement["operatingIncome"] = self.operating_income
        income_statement["operatingIncomeRatio"] = self.operating_income_ratio
        income_statement["totalOtherIncomeExpensesNet"] = self.total_other_income_expenses_net
        income_statement["incomeBeforeTax"] = self.income_before_tax
        income_statement["incomeBeforeTaxRatio"] = self.income_before_tax_ratio
        income_statement["incomeTaxExpense"] = self.income_tax_expense
        income_statement["netIncome"] = self.net_income
        income_statement["netIncomeRatio"] = self.net_income_ratio
        income_statement["eps"] = self.eps
        income_statement["epsdiluted"] = self.eps_diluted
        income_statement["weightedAverageShsOut"] = self.weighted_average_shs_out
        income_statement["weightedAverageShsOutDil"] = self.weighted_average_shs_out_dil
        return income_statement    

    def generate_cash_flow(self, date, symbol, period) -> dict:
        changeInWorkingCapital = self.account_receivable + self.accounts_payable + self.inventory + self.otherWorkingCapital
        netCashProvidedByOperatingActivities = self.net_income + self.depreciation_and_amortization + self.deferred_income_tax + self.stock_based_compensation + changeInWorkingCapital + self.other_non_cash_items
        cash_flow = {
            "date": date,
            "symbol": symbol,
            "reportedCurrency": "USD",
            "calendarYear": date.year,
            "period": period,
            "netIncome": self.net_income,
            "depreciationAndAmortization": self.depreciation_and_amortization,
            "deferredIncomeTax": self.deferred_income_tax,
            "stockBasedCompensation": self.stock_based_compensation,
            "changeInWorkingCapital": changeInWorkingCapital,
            "accountsReceivables": self.account_receivable,
            "inventory": self.inventory,
            "accountsPayables": self.accounts_payable,
            "otherWorkingCapital": self.otherWorkingCapital,
            "otherNonCashItems": self.other_non_cash_items,
            "netCashProvidedByOperatingActivities": netCashProvidedByOperatingActivities,
            "investmentsInPropertyPlantAndEquipment": self.investments_in_ppe,
            "acquisitionsNet": self.acquisitions_net,
            "purchasesOfInvestments": self.purchases_of_investments,
            "salesMaturitiesOfInvestments": self.sales_maturities_of_investments,
            "otherInvestingActivites": self.other_investing_activites,
            "netCashUsedForInvestingActivites": self.investments_in_ppe + self.acquisitions_net + self.purchases_of_investments + self.sales_maturities_of_investments + self.other_investing_activites,
            "debtRepayment": self.debtRepayment,
            "commonStockIssued": self.common_stock_issued,
            "commonStockRepurchased": self.common_stock_repurchased,
            "dividendsPaid": self.dividends_paid,
            "otherFinancingActivites": self.other_financing_activites,
            "netCashUsedProvidedByFinancingActivities": self.debtRepayment + self.common_stock_issued + self.common_stock_repurchased + self.dividends_paid + self.other_financing_activites,
            "effectOfForexChangesOnCash": 0,
            "netChangeInCash": self.cash_at_beginning_of_period - self.cash_at_end_of_period,
            "cashAtEndOfPeriod": self.cash_at_end_of_period,
            "cashAtBeginningOfPeriod": self.cash_at_beginning_of_period,
            "operatingCashFlow": netCashProvidedByOperatingActivities,
            "capitalExpenditure": self.capital_expenditures,
            "freeCashFlow": netCashProvidedByOperatingActivities - self.capital_expenditures,
        }
        return cash_flow

    def generate_balance_sheet(self, date, symbol, period) -> dict:
        totalCurrentAssets= self.cash_and_cash_equivalents + self.short_term_investments + self.net_receivables + self.inventory_balance + self.other_current_assets
        totalNonCurrentAssets = self.ppe_net + self.goodwill + self.intangible_assets + self.long_term_investments + self.taxAssets + self.otherNonCurrentAssets
        totalCurrentLiabilities = self.accounts_payable_balance + self.short_term_debt + self.taxPayables + self.deferred_revenue + self.other_current_liabilities
        totalNonCurrentLiabilities = self.long_term_debt + self.deferred_revenue_non_current + self.deferredTaxLiabilitiesNonCurrent + self.other_non_current_liabilities
        totalStockHolderEquity = self.preferred_stock + self.common_stock + self.retained_earnings + self.accumulated_other_comprehensive_income_loss + self.other_stockholder_equity
        totalLiabilitiesAndStockholdersEquity = totalCurrentLiabilities + totalNonCurrentLiabilities + totalStockHolderEquity
        balance_sheet = {
            "date": date,
            "symbol": symbol,
            "reportedCurrency": "USD",
            "calendarYear": date.year,
            "period": period,
        }
        balance_sheet["cashAndCashEquivalents"] = self.cash_and_cash_equivalents
        balance_sheet["shortTermInvestments"] = self.short_term_investments
        balance_sheet["cashAndShortTermInvestments"] = self.cash_and_cash_equivalents + self.short_term_investments
        balance_sheet["netReceivables"] = self.net_receivables 
        balance_sheet["inventory"] = self.inventory_balance
        balance_sheet["otherCurrentAssets"] = self.other_current_assets
        balance_sheet["totalCurrentAssets"] = totalCurrentAssets
        balance_sheet["propertyPlantEquipmentNet"] = self.ppe_net
        balance_sheet["goodwill"] = self.goodwill
        balance_sheet["intangibleAssets"] = self.intangible_assets
        balance_sheet["goodwillAndIntangibleAssets"] = self.goodwill + self.intangible_assets
        balance_sheet["longTermInvestments"] = self.long_term_investments
        balance_sheet["taxAssets"] = self.taxAssets
        balance_sheet["otherNonCurrentAssets"] = self.otherNonCurrentAssets
        balance_sheet["totalNonCurrentAssets"] = totalCurrentAssets
        balance_sheet["otherAssets"] = self.other_assets
        balance_sheet["totalAssets"] = totalCurrentAssets + totalNonCurrentAssets + self.other_assets
        balance_sheet["accountPayables"] = self.accounts_payable_balance
        balance_sheet["shortTermDebt"] = self.short_term_debt
        balance_sheet["taxPayables"] = self.taxPayables
        balance_sheet["deferredRevenue"] = self.deferred_revenue
        balance_sheet["otherCurrentLiabilities"] = self.other_current_liabilities
        balance_sheet["totalCurrentLiabilities"] = totalCurrentLiabilities
        balance_sheet["longTermDebt"] = self.long_term_debt
        balance_sheet["deferredRevenueNonCurrent"] = self.deferred_revenue_non_current
        balance_sheet["deferredTaxLiabilitiesNonCurrent"] = self.deferredTaxLiabilitiesNonCurrent
        balance_sheet["otherNonCurrentLiabilities"] = self.other_non_current_liabilities
        balance_sheet["totalNonCurrentLiabilities"] = totalNonCurrentLiabilities
        balance_sheet["otherLiabilities"] = self.other_liabilities
        balance_sheet["capitalLeaseObligations"] = self.capitalLeaseObligations
        balance_sheet["totalLiabilities"] = totalCurrentLiabilities + totalNonCurrentLiabilities + self.other_liabilities + self.capitalLeaseObligations
        balance_sheet["preferredStock"] = self.preferred_stock
        balance_sheet["commonStock"] = self.common_stock
        balance_sheet["retainedEarnings"] = self.retained_earnings
        balance_sheet["accumulatedOtherComprehensiveIncomeLoss"] = self.accumulated_other_comprehensive_income_loss
        balance_sheet["othertotalStockholdersEquity"] = self.other_stockholder_equity
        balance_sheet["totalStockholdersEquity"] = totalStockHolderEquity
        balance_sheet["totalEquity"] = totalStockHolderEquity
        balance_sheet["totalLiabilitiesAndStockholdersEquity"] = totalLiabilitiesAndStockholdersEquity
        balance_sheet["minorityInterest"] = self.minority_interest
        balance_sheet["totalLiabilitiesAndTotalEquity"] = totalLiabilitiesAndStockholdersEquity+ self.minority_interest
        balance_sheet["totalInvestments"] = self.total_investments
        balance_sheet["totalDebt"] = self.total_debt
        balance_sheet["netDebt"] = self.total_debt - self.cash_and_cash_equivalents        
        return balance_sheet
