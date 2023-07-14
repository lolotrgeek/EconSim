from .AgentProcess import Agent
from datetime import datetime, timedelta

class Government(Agent):
    def __init__(self, initial_balance=10000000, requester=None):
        super().__init__("Government", initial_balance, requester=requester)
        self.long_term_capital_gains_tax_rate = None
        self.short_term_capital_gains_tax_rate = None
        self.current_date = datetime(1700,1,1)

    async def collect_taxes(self, current_date, tax_rate):
        agents = await self.requests.get_agents()
        for agent in agents:
            tax_bill = 0
            for position in agent['positions']:
                position['transactions'].sort(key=lambda x: x['dt'])
 
                for idx, transaction in enumerate(position['transactions']):
                    if transaction['dt'] + timedelta(days=365) < current_date:
                        tax_rate = self.long_term_capital_gains_tax_rate
                    else:
                        tax_rate = self.short_term_capital_gains_tax_rate
                    if transaction['cash_flow'] > 0:
                        tax_bill += transaction['exits']['pnl'] * tax_rate
            await self.requests.remove_cash(agent['name'], tax_bill)

    async def set_reserve_requirement(self, reserve_requirement):
        """Sets requirement for how much money the banks must keep in reserve.

        Args:
            reserve_requirement (float): the reserve requirement as a percentage of deposits.
        """
        pass

    async def print_money(self, amount):
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
    
    async def issue_treasury_notes(self, face_value, maturity_years, quantity):
        """Issues treasury notes to the banking system.

        Args:
            face_value (float): the face value of each note.
            maturity_years (int): the maturity of each note in years.
            quantity (int): the number of notes to issue.
        """
        pass

    async def loan_money(self, amount, rate, recipient):
        """Loans money to another agent.

        Args:
            amount (float): the amount of money to loan.
            rate (float): the interest rate of the loan.
            recipient (Agent): the recipient of the loan.
        """
        pass

    async def next(self):
        """The government's next action.

        Args:
            current_date (datetime): the current date.
        """
        
        # if the date is april 15th, calculate tax bills
        if self.current_date.month == 4 and self.current_date.day == 15:
            print('collecting taxes...')
            await self.collect_taxes(self.current_date, self.long_term_capital_gains_tax_rate)