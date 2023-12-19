import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
from datetime import datetime, timedelta
from .operations import Operations
from source.utils._utils import string_to_time
from source.Archive import Archive

class PublicCompany:
    """
    Runs all public companies as a process Generating financial reports, distributing dividends, and issuing shares
    """
    def __init__(self, name, startdate, requests):
        self.name = name
        self.symbol = name[:3].upper()
        self.startdate = startdate
        self.currentdate = startdate
        self.quarter_length = 13
        self.next_quarter = {"period": "Q1", "date": self.currentdate + timedelta(weeks=self.quarter_length)}
        self.shares_issued = []
        self.shares_repurchased = 0
        self.shareholders = []
        self.market_cap = random.choice(['large', 'medium', 'small', 'micro'])
        self.operations = Operations(self.market_cap)
        self.balance_sheet = None
        self.income_statement = None
        self.cash_flow = None
        self.ex_dividend_date = None
        self.dividend_payment_date = None
        self.balance_sheet_archive = Archive(self.symbol+"_balance_sheet")
        self.income_statement_archive = Archive(self.symbol+"_income_statement")
        self.cash_flow_archive = Archive(self.symbol+"_cash_flow")
        self.dividends_to_distribute = 0
        self.requests = requests

    def __str__(self):
        return f"PublicCompany({self.name}, {self.symbol}, {self.startdate}, {self.currentdate}, {self.shareholders}, {self.balance_sheet}, {self.income_statement}, {self.cash_flow}, {self.ex_dividend_date}, {self.dividend_payment_date}, {self.dividends_to_distribute})"
    
    def __repr__(self):
        return f"PublicCompany({self.name}, {self.symbol}, {self.startdate}, {self.currentdate}, {self.shareholders}, {self.balance_sheet}, {self.income_statement}, {self.cash_flow}, {self.ex_dividend_date}, {self.dividend_payment_date}, {self.dividends_to_distribute})"
    
    def to_dict(self):
        return {
            "name": self.name,
            "symbol": self.symbol,
            "startdate": self.startdate,
            "currentdate": self.currentdate,
            "next_quarter": self.next_quarter,
            "dividends_to_distribute": self.dividends_to_distribute,
            "dividend_payment_date": self.dividend_payment_date,
            "ex_dividend_date": self.ex_dividend_date,
        }        

    async def initial_operate_and_report(self) -> None:
        await self.operate_and_report("annual")
        if self.dividends_to_distribute > 0:
            self.ex_dividend_date = self.currentdate + timedelta(weeks=2)
            self.dividend_payment_date = self.ex_dividend_date + timedelta(weeks=4)  

    async def issue_initial_shares(self, shares, price, ticker='', attempts = 1) -> None:
        if ticker == '': ticker = self.symbol
        issue_shares = await self.requests.create_asset(ticker, qty=shares, seed_price=price, seed_bid=price * 0.99, seed_ask=price * 1.01)
        if issue_shares == {"error" :f'asset {self.symbol} already exists'}:
            if attempts <= 3:
                ticker = self.symbol + self.name[:3+attempts]
                self.symbol = ticker
                return await self.issue_initial_shares(shares, price, ticker, attempts+1)
            else:
                raise Exception(f"Failed to issue shares for {self.symbol}")
        else:
            self.shares_issued.append({"shares": shares, "price": price, "value": shares*price, "date": self.currentdate})

    async def issue_shares(self, shares, price) -> None:
        #TODO: adding shares to an existing asset
        pass

    async def buyback_shares(self, shares, price) -> None:
        await self.requests.add_cash("init_seed_"+self.symbol, shares * price, "buyback")
        await self.requests.limit_buy(self.symbol, price, shares, "init_seed_"+self.symbol)
        #TODO: implement as a list like shares_issued
        self.shares_repurchased += shares        

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
        self.balance_sheet = self.operations.generate_balance_sheet(date, self.symbol, period)
        self.income_statement = self.operations.generate_income_statement(date, self.symbol, period)
        self.cash_flow = self.operations.generate_cash_flow(date, self.symbol, period)
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

    async def value_of_shares(self, period) -> float:
        outstanding_shares = await self.requests.get_outstanding_shares(self.symbol)
        mid_price = await self.requests.get_midprice(self.symbol)
        if outstanding_shares == 0: outstanding_shares = 1 # NOTE: outstanding shares cannot be 0
        if mid_price == 0: mid_price = 0.01 # NOTE: fair value cannot be 0
        outstanding_shares_value = mid_price * outstanding_shares
        
        shares_issued_value = 0
        for shares_issued in self.shares_issued:
            if period == 'annual' and shares_issued["date"].year == self.currentdate.year: 
                shares_issued_value += shares_issued["value"]
            else:
                beginning_of_quarter_date = self.currentdate - timedelta(weeks=self.quarter_length)
                if shares_issued["date"] >= beginning_of_quarter_date: 
                    shares_issued_value += shares_issued["value"]
        
        # print(f"midprice: {mid_price} outstanding_shares: {outstanding_shares}, shares_issued_value: {shares_issued_value}, outstanding_shares_value: {outstanding_shares_value}, period {period}")
        return outstanding_shares_value, shares_issued_value

    async def operate_and_report(self, period) -> None:
        outstanding_shares_value, shares_issued_value = await self.value_of_shares(period)
        self.operations.next(outstanding_shares_value, shares_issued_value, self.shares_repurchased)
        
        await self.generate_financial_report(self.currentdate, period)
        await self.archive_reports(period)

        if self.dividends_to_distribute > 0:
            self.ex_dividend_date = self.ex_dividend_date = self.currentdate + timedelta(weeks=2)
            self.dividend_payment_date = self.ex_dividend_date + timedelta(weeks=4)

    async def archive_reports(self, period) -> None:
        self.balance_sheet_archive.put(str(self.currentdate), {"period": period, "report": self.balance_sheet})
        self.income_statement_archive.put(str(self.currentdate), {"period": period, "report": self.income_statement})
        self.cash_flow_archive.put(str(self.currentdate), {"period": period, "report": self.cash_flow})

    async def next(self, current_date) -> None:
        self.currentdate = current_date

        if self.currentdate >= self.next_quarter["date"]:
            await self.operate_and_report(self.next_quarter["period"])
            if self.next_quarter["period"] == "Q1": period = "Q2"
            elif self.next_quarter["period"] == "Q2": period = "Q3"
            elif self.next_quarter["period"] == "Q3": period = "Q4"
            elif self.next_quarter["period"] == "Q4": period = "Q1"
            self.next_quarter = {"period": period, "date": self.currentdate + timedelta(weeks=self.quarter_length)}

        elif self.currentdate.month == 12 and self.currentdate.day == 31:
            await self.operate_and_report("annual")

        if self.currentdate == self.dividend_payment_date:
            self.shareholders = await self.requests.get_agents_positions(self.symbol)
            eligible_shareholders = await self.get_eligible_shareholders()
            await self.distribute_dividends(eligible_shareholders, self.dividends_to_distribute)
            self.dividends_to_distribute = 0
            