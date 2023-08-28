import random

#TODO: ensure that if revenue is less than the expenses that debt and/or financing is increased to cover the difference

class Revenue():
    def __init__(self, market_cap) -> None:
        self.revenue = 0
        if market_cap == 'large': self.revenue = random.randint(1_000_000_000, 1_000_000_000_000)
        elif market_cap == 'medium': self.revenue = random.randint(100_000_000, 1_000_000_000)
        elif market_cap == 'small': self.revenue = random.randint(1_000_000, 100_000_000)
        else: self.revenue = random.randint(1_000, 1_000_000)
        self.deferred_revenue = self.revenue * random.uniform(0.1, 0.2)
        self.deferred_revenue_non_current = self.revenue * random.uniform(0.1, 0.2)
        self.net_receivable = self.revenue * random.uniform(0.1, 0.2)

    def nextRevenue(self, period):
        payments_received = self.net_receivable * random.uniform(0.01, 0.2)
        self.net_receivable -= payments_received
        next_revenue = self.revenue * random.uniform(0.9, 1.1) 
        
        # how much of revenue is deferred
        self.deferred_revenue += next_revenue * random.uniform(-0.2, 0.2)
        self.deferred_revenue_non_current += next_revenue * random.uniform(-0.2, 0.2)

        # generate the receivables for this period
        self.account_receivable = next_revenue * random.uniform(0.0, 0.1) # the receviables for this period
        self.net_receivable += self.account_receivable # the remaining receivables from this and all prior periods
        
        self.revenue = next_revenue

class Expenses():
    def __init__(self, market_cap) -> None:
        self.expenses = 0
        if market_cap == 'large': self.expenses = random.randint(1_000_000_000, 1_000_000_000_000)
        elif market_cap == 'medium': self.expenses = random.randint(100_000_000, 1_000_000_000)
        elif market_cap == 'small': self.expenses = random.randint(1_000_000, 100_000_000)
        else: self.expenses = random.randint(1_000, 1_000_000)        
        self.cost_of_revenue = 0
        self.research_and_development_expenses = 0
        self.general_and_administrative_expenses = 0
        self.selling_and_marketing_expenses = 0
        self.selling_general_and_administrative_expenses = 0
        self.other_expenses = 0
        self.totalOtherIncomeExpensesNet = 0
        self.accounts_payable = 0
        self.accounts_payable_balance = 0

    def nextExpenses(self, capital):
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
        self.totalOtherIncomeExpensesNet = self.cost_of_revenue - (self.research_and_development_expenses + self.general_and_administrative_expenses + self.selling_and_marketing_expenses + self.selling_general_and_administrative_expenses + self.other_expenses)        
        
        # generate the payables for this period
        self.accounts_payable = self.cost_of_revenue * random.uniform(0.1, 0.2)
        self.accounts_payable_balance += self.accounts_payable

        self.expenses = next_expenses

class Debt():
    def __init__(self, market_cap) -> None:
        self.debt = 0
        if market_cap == 'large': self.debt = random.randint(1_000_000_000, 1_000_000_000_000)
        elif market_cap == 'medium': self.debt = random.randint(100_000_000, 1_000_000_000)
        elif market_cap == 'small': self.debt = random.randint(1_000_000, 100_000_000)
        else: self.debt = random.randint(1_000, 1_000_000)
        self.short_term_debt = self.debt * random.uniform(0.1, 0.5)
        self.long_term_debt = self.debt - self.short_term_debt
        self.interest_rate = random.uniform(0.001, 0.1)
        self.debtRepayment = 0
        self.interestExpense = 0

    def nextDebt(self, revenue, expenses):
        short_term_debt_interest = self.interest_rate * self.short_term_debt
        long_term_debt_interest = self.interest_rate * self.long_term_debt
        self.interestExpense = short_term_debt_interest + long_term_debt_interest
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

        self.debt = self.short_term_debt + self.long_term_debt

class Tax():
    def __init__(self, tax_rate=0.15) -> None:
        self.tax_rate = tax_rate
        self.taxAssets = 0
        self.income_tax_expense = 0
        self.deferred_income_tax = 0
        self.deferredTaxLiabilitiesNonCurrent = 0
        self.taxPayables = 0


    def nextTax(self, period, income_before_tax):
        # calculate taxes
        self.taxPayables = income_before_tax * self.tax_rate

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

class Capital():
    def __init__(self, market_cap) -> None:
        self.capital = 0
        if market_cap == 'large': self.capital = random.randint(1_000_000_000, 1_000_000_000_000)
        elif market_cap == 'medium': self.capital = random.randint(100_000_000, 1_000_000_000)
        elif market_cap == 'small': self.capital = random.randint(1_000_000, 100_000_000)
        else: self.capital = random.randint(1_000, 1_000_000)        
        self.inventory = 0
        self.investments_in_ppe = 0
        self.ppe_net = 0
        self.depreciation_and_amortization_current = 0
        self.depreciation_and_amortization = 0
        self.capitalLeaseObligations = 0
        self.otherWorkingCapital = 0
        self.inventory_balance = 0

    def nextCapital(self, cost_of_revenue):
        self.inventory = self.capital * random.uniform(0.1, 0.2)
        self.inventory_balance += self.inventory

        self.investments_in_ppe = self.capital * random.uniform(0.1, 0.2)
        self.ppe_net += self.investments_in_ppe

        self.depreciation_and_amortization_current = self.investments_in_ppe * random.uniform(0.01, 0.1)
        self.depreciation_and_amortization = self.ppe_net * random.uniform(0.01, 0.1)

        self.otherWorkingCapital = self.capital * random.uniform(0.1, 0.2)
        self.capitalLeaseObligations = cost_of_revenue * random.uniform(0.3, 0.5)

class Investment():
    def __init__(self, market_cap) -> None:
        self.investments = 0
        if market_cap == 'large': self.investments = random.randint(1_000_000_000, 1_000_000_000_000)
        elif market_cap == 'medium': self.investments = random.randint(100_000_000, 1_000_000_000)
        elif market_cap == 'small': self.investments = random.randint(1_000_000, 100_000_000)
        else: self.investments = random.randint(1_000, 1_000_000)
        self.purchases_of_investments = 0
        self.acquisitions_net = 0
        self.other_investing_activites = 0
        self.short_term_investments = 0
        self.long_term_investments = 0
        self.goodwill = 0
        self.otherNonCurrentAssets = 0
        self.sales_maturities_of_investments = 0

    def nextInvestment(self, cash_to_invest):
        # sell off some investments
        if self.investments > 0:
            self.sales_maturities_of_investments = self.investments * random.uniform(0.01, 0.2)
            self.investments -= self.sales_maturities_of_investments
        
        next_investments = cash_to_invest
        
        # buy more investments
        self.purchases_of_investments = next_investments * random.uniform(0.01, 0.2)
        self.acquisitions_net = next_investments * random.uniform(0.01, 0.2)
        self.other_investing_activites = next_investments * random.uniform(0.01, 0.2)

        self.short_term_investments = self.purchases_of_investments * random.uniform(0.1, 0.8)
        self.long_term_investments = self.purchases_of_investments - self.short_term_investments + self.acquisitions_net

        self.goodwill = self.acquisitions_net * random.uniform(0.1, 0.2)

        self.otherNonCurrentAssets = self.other_investing_activites * random.uniform(0.1, 0.2)

        self.investments = next_investments

class Equity():
    def __init__(self, market_cap) -> None:
        self.equity = 0
        if market_cap == 'large': self.equity = random.randint(1_000_000_000, 1_000_000_000_000)
        elif market_cap == 'medium': self.equity = random.randint(100_000_000, 1_000_000_000)
        elif market_cap == 'small': self.equity = random.randint(1_000_000, 100_000_000)
        else: self.equity = random.randint(1_000, 1_000_000)
        self.stock_based_compensation = 0
        self.preferred_stock = 0
        self.common_stock = 0
        self.common_stock_repurchased = 0
        self.common_stock_issued = 0
        self.accumulated_other_comprehensive_income_loss = 0
        self.other_stockholder_equity = 0

    def nextEquity(self, shares_issued, shares_repurchased, ):
        next_equity = self.equity * random.uniform(0.9, 1.1)

        compensate_with_stock = random.randint(0, 5)
        if compensate_with_stock == 5:
            self.stock_based_compensation = next_equity * random.uniform(0.01, 0.1)
        
        issue_preferred_stock = random.randint(0, 5)
        if issue_preferred_stock == 5:
            self.preferred_stock = next_equity * random.uniform(0.01, 0.1)

        self.common_stock_issued = shares_issued 
        self.common_stock_repurchased = shares_repurchased
        self.common_stock += shares_issued  - shares_repurchased

        if self.common_stock < 0:
            self.accumulated_other_comprehensive_income_loss += self.common_stock_issued - self.common_stock_repurchased
        else:
            self.accumulated_other_comprehensive_income_loss = 0

        self.other_stockholder_equity = next_equity * random.uniform(0.01, 0.1)
        
class NonCash():
    def __init__(self) -> None:
        self.other_non_cash_items = 0
        self.other_current_assets = 0
        self.intangible_assets = 0
        self.other_assets = 0

    def nextNonCash(self, revenue, expenses, investments):
        self.other_current_assets = revenue * random.uniform(0.01, 0.1)
        self.intangible_assets = expenses * random.uniform(0.01, 0.1)
        self.other_assets = investments * random.uniform(0.01, 0.1)

        self.other_non_cash_items = self.other_current_assets + self.intangible_assets + self.other_assets

class Cash():
    def __init__(self) -> None:
        self.net_income = 0
        self.retained_earnings = 0
        self.dividends_paid = 0
        self.cash_and_cash_equivalents = 0
        self.interestIncome = 0

    def nextCash(self, revenue, expenses, investments, debt, tax, capital, equity):
        self.net_income = revenue - expenses + investments - debt - tax - capital - equity
        self.retained_earnings += self.net_income
        self.dividends_paid = self.retained_earnings * random.uniform(0.01, 0.8)
        self.cash_and_cash_equivalents = self.net_income - self.dividends_paid
        self.interestIncome = capital * random.uniform(0.01, 0.1)

class Financing():
    def __init__(self):
        self.other_financing_activites = 0
        self.other_liabilities = 0
        self.other_current_liabilities = 0
        self.other_non_current_liabilities = 0

    def nextFinancing(self, investments, equity):
        self.other_liabilities = investments * random.uniform(0.01, 0.1)
        self.other_current_liabilities = equity * random.uniform(0.01, 0.1)
        self.other_non_current_liabilities = equity * random.uniform(0.01, 0.1)
        self.other_financing_activites = self.other_liabilities + self.other_current_liabilities + self.other_non_current_liabilities