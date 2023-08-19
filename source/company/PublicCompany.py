import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from datetime import datetime, timedelta
from .balance_sheet import generate_fake_balance_sheet
from .income import generate_fake_income_statement
from .cash_flow import generate_fake_cash_flow
from source.utils._utils import string_to_time

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
        await self.generate_financial_report(self.currentdate, "annual")
        if self.dividends_to_distribute > 0:
            self.ex_dividend_date = self.currentdate + timedelta(weeks=2)
            self.dividend_payment_date = self.ex_dividend_date + timedelta(weeks=4)        

    async def issue_initial_shares(self, shares, price, ticker='', attempts = 1) -> None:
        if ticker == '': ticker = self.symbol
        shares_issued = await self.requests.create_asset(ticker, qty=shares, seed_price=price, seed_bid=price * 0.99, seed_ask=price * 1.01)
        if shares_issued == {"error" :f'asset {self.symbol} already exists'}:
            if attempts <= 3:
                ticker = self.symbol + self.name[:3+attempts]
                await self.issue_initial_shares(shares, price, ticker, attempts+1)
            else:
                raise Exception(f"Failed to issue shares for {self.symbol}")

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

    async def generate_financial_report(self, date, period) -> None:
        #TODO: use the prior period's financials to generate the current period's financials, integrate lower probabilities for large changes
        self.balance_sheet = generate_fake_balance_sheet(date, self.symbol, period)
        self.income_statement = generate_fake_income_statement(date, self.symbol, period)
        self.cash_flow = generate_fake_cash_flow(self.balance_sheet['retainedEarnings'], date, self.symbol, period)
        self.dividends_to_distribute = self.cash_flow["dividendsPaid"] * -1
    
    async def distribute_dividends(self, eligible_shareholders, dividends_paid) -> None:
        outstanding_shares = await self.requests.get_outstanding_shares(self.symbol)
        for eligible_shareholder in eligible_shareholders:
            eligible_shares = eligible_shareholder["shares"]
            dividend = (int(eligible_shares) / int(outstanding_shares)) * dividends_paid
            await self.requests.add_cash(eligible_shareholder["name"], dividend, "dividend")
    
    async def get_eligible_shareholders(self) -> list:
        eligible_shareholders = []
        for shareholder in self.shareholders:
            if shareholder["agent"] == "init_seed_"+self.symbol:
                continue
            for position in shareholder["positions"]:
                # ignore positions bought after exdividend date
                if string_to_time(position["dt"]) < self.ex_dividend_date:
                    # calculate the number of shares eligible for dividends
                    eligible_shareholder = {'name': shareholder['agent'] ,'shares':0}
                    shares = 0
                    # bought before exdividend date
                    for enter in position["enters"]:
                        if string_to_time(enter["dt"]) < self.ex_dividend_date:
                            shares += enter["initial_qty"]
                            # check if we sold any of the entered shares before or on the exdividend date
                            for exits in position['exits']:
                                if exits["enter_id"] == enter["id"] and string_to_time(exits["dt"]) <= self.ex_dividend_date:
                                    shares -= exits["qty"]
                    
                    eligible_shareholder["shares"] = shares
                    if shares > 0:       
                        eligible_shareholders.append(eligible_shareholder)
        return eligible_shareholders
    
    async def quarterly_things(self, quarter) -> None:
        await self.generate_financial_report(self.currentdate, quarter)
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
            
