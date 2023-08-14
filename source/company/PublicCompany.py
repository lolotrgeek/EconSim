from datetime import datetime, timedelta
from .balance_sheet import generate_fake_balance_sheet
from .income import generate_fake_income_statement
from .cash_flow import generate_fake_cash_flow

class PublicCompany:
    """
    Runs all public companies as a process Generating financial reports, distributing dividends, and issuing shares
    """
    def __init__(self, name, startdate, requester):
        self.name = name
        self.symbol = name[:3].upper()
        self.startdate = startdate
        self.currentdate = startdate
        self.quarters = [
            startdate + timedelta(weeks=13),
            startdate + timedelta(weeks=26),
            startdate + timedelta(weeks=39),
            startdate + timedelta(weeks=52)
        ]
        self.outstanding_shares = 0
        self.shareholders = []
        self.balance_sheet = None
        self.income_statement = None
        self.cash_flow = None
        self.ex_dividend_date = None
        self.dividend_payment_date = None
        self.dividends_to_distribute = 0
        self.requests = requester

    def __str__(self):
        return f"PublicCompany({self.name}, {self.symbol}, {self.startdate}, {self.currentdate}, {self.outstanding_shares}, {self.shareholders}, {self.balance_sheet}, {self.income_statement}, {self.cash_flow}, {self.ex_dividend_date}, {self.dividend_payment_date}, {self.dividends_to_distribute})"
    
    def __repr__(self):
        return f"PublicCompany({self.name}, {self.symbol}, {self.startdate}, {self.currentdate}, {self.outstanding_shares}, {self.shareholders}, {self.balance_sheet}, {self.income_statement}, {self.cash_flow}, {self.ex_dividend_date}, {self.dividend_payment_date}, {self.dividends_to_distribute})"
    
    def to_dict(self):
        return {
            "name": self.name,
            "symbol": self.symbol,
            "startdate": self.startdate,
            "currentdate": self.currentdate,
        }        

    async def initial_financials(self) -> None:
        await self.generate_financial_report(self.currentdate, "annual", self.symbol)
        if self.dividends_to_distribute > 0:
            self.ex_dividend_date = self.currentdate + timedelta(weeks=2)
            self.dividend_payment_date = self.ex_dividend_date + timedelta(weeks=4)        

    async def issue_initial_shares(self, shares, price) -> None:
        await self.requests.create_asset(self.symbol, shares, price, price * 0.99, price * 1.01)

    async def issue_shares(self, shares, price) -> None:
        #TODO: adding shares to an existing asset
        pass

    async def buyback_shares(self, shares, price) -> None:
        #TODO: place a market order to buy shares
        pass

    async def split_shares(self, ratio) -> None:
        #TODO: split shares
        pass

    async def cease_operations(self) -> None:
        #TODO: bancrupt company, delist, and liquidate all assets, pay off all debts, and distribute remaining cash to shareholders
        pass

    async def delist(self) -> None:
        #TODO: delist company on exchange, meaning no more shares can be bought or sold
        pass

    async def generate_financial_report(self, date, period, symbol) -> None:
        #TODO: use the prior period's financials to generate the current period's financials, integrate lower probabilities for large changes
        self.balance_sheet = generate_fake_balance_sheet(date, symbol, period)
        self.income_statement = generate_fake_income_statement(date, symbol, period)
        self.cash_flow = generate_fake_cash_flow(self.balance_sheet['retainedEarnings'], date, symbol, period)
        self.dividends_to_distribute = self.cash_flow["dividendsPaid"] * -1
    
    async def distribute_dividends(self, eligible_shareholders, dividends_paid) -> None:
        total_shares_held_by_all_shareholders = sum(sum(shareholder["shares"]) for shareholder in self.shareholders)
        for eligible_shareholder in eligible_shareholders:
            eligible_shares = sum(eligible_shareholder["shares"])
            dividend = (eligible_shares / total_shares_held_by_all_shareholders) * dividends_paid
            eligible_shareholder["dividend"] = dividend
            self.requests.add_cash(eligible_shareholder["name"], dividend)
    
    async def get_eligible_shareholders(self) -> list:
        eligible_shareholders = []
        for shareholder in self.shareholders:
            for position in shareholder["positions"]:
                # ignore positions bought after exdividend date
                if position["dt"] <= self.ex_dividend_date:
                    # calculate the number of shares eligible for dividends
                    eligible_shareholder = {'name': shareholder['agent'] ,'shares':0}
                    for transaction in position["transactions"]:
                        if transaction["dt"] <= self.ex_dividend_date:
                            eligible_shareholder["shares"] += transaction["qty"]
                    eligible_shareholders.append(eligible_shareholder)
        return eligible_shareholders
    
    async def quarterly_things(self, quarter) -> None:
        await self.generate_financial_report(self.currentdate, quarter, self.symbol)
        if self.dividends_to_distribute > 0:
            self.ex_dividend_date = self.ex_dividend_date = self.currentdate + timedelta(weeks=2)
            self.dividend_payment_date = self.ex_dividend_date + timedelta(weeks=4)

    async def next(self, current_date) -> None:
        self.currentdate = current_date
        
        if self.currentdate == self.quarters[0]:
            await self.quarterly_things("Q1")
        elif self.currentdate == self.quarters[1]:
            await self.quarterly_things("Q2")
        elif self.currentdate == self.quarters[2]:
            await self.quarterly_things("Q3")
        elif self.currentdate == self.quarters[3]:
            await self.quarterly_things("Q4")

        if self.currentdate == self.dividend_payment_date:
            self.shareholders = await self.requests.get_agents_positions(self.symbol)
            eligible_shareholders = await self.get_eligible_shareholders()
            await self.distribute_dividends(eligible_shareholders, self.dividends_to_distribute)
            self.dividends_to_distribute = 0
            
