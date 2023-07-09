import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from datetime import datetime, timedelta
from .balance_sheet import generate_fake_balance_sheet
from .income import generate_fake_income_statement
from .cash_flow import generate_fake_cash_flow

class PublicCompany:
    """
    Runs all public companies as a process Generating financial reports, distributing dividends, and issuing shares
    """
    def __init__(self, name, initial_price, startdate, requester):
        self.name = name
        self.symbol = name[:3].upper()
        self.price = initial_price
        self.startdate = startdate
        self.currentdate = startdate
        self.quarters = [
            datetime(startdate.year, startdate.month+3, startdate.day), 
            datetime(startdate.year, startdate.month+6, startdate.day), 
            datetime(startdate.year, startdate.month+9, startdate.day), 
            datetime(startdate.year, startdate.month+12, startdate.day)
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
        self.generate_financial_report(self.currentdate, "annual", self.symbol)
        if self.dividends_to_distribute > 0:
            self.ex_dividend_date = datetime(self.currentdate.year, self.currentdate.month+1, self.currentdate.day)
            self.dividend_payment_date = self.ex_dividend_date + timedelta(weeks=4)

    #TODO: make all actions below alter the company's financials

    async def initial_shares(self, shares, price):
        self.price = price
        self.requests.create_asset(self.symbol, shares, price, price * 0.99, price * 1.01)

    async def issue_shares(self, shares, price):
        #TODO: this needs to be a special sell order similar to that in create_asset
        pass

    async def buyback_shares(self, shares, price):
        #TODO: place a market order to buy shares
        pass

    async def split_shares(self, ratio):
        #TODO: split shares
        pass

    async def cease_operations(self):
        #TODO: bancrupt company, delist, and liquidate all assets, pay off all debts, and distribute remaining cash to shareholders
        pass

    async def delist(self):
        #TODO: delist company on exchange, meaning no more shares can be bought or sold
        pass

    async def generate_financial_report(self, date, period, symbol):
        #TODO: use the prior period's financials to generate the current period's financials, integrate lower probabilities for large changes
        self.balance_sheet = generate_fake_balance_sheet(date, symbol, period)
        self.income_statement = generate_fake_income_statement(date, symbol, period)
        self.cash_flow = generate_fake_cash_flow(self.balance_sheet['retainedEarnings'], date, symbol, period)
        self.dividends_to_distribute = self.income_statement["dividendsPaid"] * -1
    
    async def distribute_dividends(self, eligible_shareholders, dividends_paid):
        total_shares = sum(sum(shareholder["shares"]) for shareholder in self.shareholders)
        for shareholder in eligible_shareholders:
            shares = sum(shareholder["shares"])
            dividend = (shares / total_shares) * dividends_paid
            shareholder["dividend"] = dividend
            self.requests.add_cash(shareholder["name"], dividend)
    
    async def get_eligible_shareholders(self):
        eligible_shareholders = []
        for shareholder in self.shareholders:
            for position in self.shareholders["positions"]:
                # ignore positions bought after exdividend date
                if position["dt"] > self.ex_dividend_date:
                    shareholder["positions"].remove(position)
                else:
                    # calculate the number of shares eligible for dividends
                    eligible_shareholder = {'name': shareholder['agent'] ,'shares':0}
                    for transaction in position["transactions"]:
                        if transaction["dt"] < self.ex_dividend_date:
                            eligible_shareholder["shares"] += transaction["qty"]
                    eligible_shareholders.append(eligible_shareholder)
        return eligible_shareholders
    
    async def quarterly_things(self, quarter):
        await self.generate_financial_report(self.currentdate, quarter, self.symbol)
        if self.dividends_to_distribute > 0:
            self.ex_dividend_date = datetime(self.currentdate.year, self.currentdate.month+1, self.currentdate.day)
            self.dividend_payment_date = self.ex_dividend_date + timedelta(weeks=4)
    
    async def next(self, current_date):
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
            self.distribute_dividends(eligible_shareholders, self.dividends_to_distribute)
            self.dividends_to_distribute = 0
            
