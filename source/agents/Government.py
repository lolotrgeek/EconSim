from .Agent import Agent
from datetime import datetime, timedelta
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source.Instruments.Tax import Tax
from source.utils._utils import string_to_time
from source.Archive import Archive
from source.utils.logger import Logger

class Government(Agent):
    def __init__(self, initial_balance=10000000, requester=None):
        super().__init__("Government", initial_balance, requester=requester)
        self.current_date = datetime(1700,1,1)
        self.taxes_last_collected = {"date": self.current_date, "amount": 0}
        self.max_tax_records = 100000 #NOTE: this needs to be at least larger than the amount of agents in the simulation
        self.tax_records = []
        self.taxes = Tax()
        self.back_taxes = [] #NOTE: taxes owed by agents that have not been paid yet
        self.tax_records_archive = Archive('tax_records')
        self.logger = Logger('Government')

    async def collect_taxes(self) -> None:
        self.taxes_last_collected['amount'] = 0
        self.logger.info("Getting Taxable Events")
        taxable_events = await self.requests.get_taxable_events()
        if 'error' in taxable_events:
            self.logger.error(taxable_events['error'])
            return
        self.logger.info(f"Found Taxable Events {len(taxable_events)}")
        for event in taxable_events:
            long_term_capital_gains = 0
            short_term_capital_gains = 0
            for taxable_event in event['taxable_events']:
                if string_to_time(taxable_event['exit_date']).year != self.current_date.year:
                    continue
                if taxable_event['pnl'] > 0:
                    if string_to_time(taxable_event['exit_date']) - string_to_time(taxable_event['enter_date']) >= timedelta(days=365):
                        long_term_capital_gains += taxable_event['pnl']
                    else:
                        short_term_capital_gains += taxable_event['pnl']
            short_term_tax = await self.taxes.calculate_tax(short_term_capital_gains, 'ordinary', debug=False)
            long_term_tax = await self.taxes.calculate_tax(long_term_capital_gains, 'long_term', debug=False)
            local_tax = await self.taxes.calculate_tax(long_term_capital_gains + short_term_capital_gains, 'state', debug=False)
            self.taxes_last_collected['amount'] += long_term_tax['amount'] + short_term_tax['amount'] + local_tax['amount']
            self.logger.info(f"Collecting Taxes from {event['agent']} for {long_term_tax['amount'] + short_term_tax['amount']}")
            tax_record = {"date": self.current_date, "agent": event['agent'], "long_term": long_term_tax['amount'], "short_term": short_term_tax['amount'], "local": local_tax['amount']}
            remove = await self.requests.remove_cash(event['agent'], long_term_tax['amount'] + short_term_tax['amount'], 'taxes')
            if 'error' in remove:
                self.back_taxes.append(tax_record)
                self.logger.error(remove['error'], event['agent'])
                continue
            else:
                self.tax_records.append(tax_record)
        self.logger.info("Successfully Collected Taxes")
            

    async def set_reserve_requirement(self, reserve_requirement) -> None:
        """Sets requirement for how much money the banks must keep in reserve.

        Args:
            reserve_requirement (float): the reserve requirement as a percentage of deposits.
        """
        pass

    async def print_money(self, amount) -> None:
        """Creates money by increasing the government's balance.

        Args:
            amount (float): the amount of money to create.
        """
        pass

        """Sends money to another agent.

        Args:
            amount (float): the amount of money to send.
            recipient (Agent): the recipient of the money.
        """
        pass
    
    async def issue_treasury_notes(self, face_value, maturity_years, quantity) -> None:
        """Issues treasury notes to the banking system.

        Args:
            face_value (float): the face value of each note.
            maturity_years (int): the maturity of each note in years.
            quantity (int): the number of notes to issue.
        """
        pass

    async def loan_money(self, amount, rate, recipient) -> None:
        """Loans money to another agent.

        Args:
            amount (float): the amount of money to loan.
            rate (float): the interest rate of the loan.
            recipient (Agent): the recipient of the loan.
        """
        pass

    async def archive_tax_records(self):
        self.tax_records_archive.put(str(self.current_date.year), self.tax_records)
        self.tax_records = []


    async def collect_back_taxes(self):
        for back_tax in self.back_taxes:
            remove = await self.requests.remove_cash(back_tax['agent'], back_tax['long_term'] + back_tax['short_term'], 'taxes')
            if 'error' in remove:
                self.logger.error(remove['error'], back_tax['agent'])
                continue
            else:
                self.tax_records.append(back_tax)
                self.back_taxes.remove(back_tax)    

    async def next(self) -> None:
        """The government's next action.

        Args:
            current_date (datetime): the current date.
        """
        # attempt to collect back taxes once per month
        if self.current_date.month != self.taxes_last_collected['date'].month and self.current_date.day == 1 and self.current_date.hour == 12 and self.current_date.minute == 0 and self.current_date.second == 0:
            self.logger.info(f"Collecting back taxes on {self.current_date}")
            await self.collect_back_taxes()

        
        # check if taxes have been collected this year
        if self.current_date.year != self.taxes_last_collected['date'].year and self.current_date.month >= 4 and self.current_date.day >= 15:
            self.logger.info(f"Collecting taxes on {self.current_date}")
            await self.archive_tax_records()
            self.taxes_last_collected['date'] = self.current_date
            await self.collect_taxes()
            