import random
from .AgentProcess import Agent
from datetime import datetime

class Bank(Agent):
    """
    Holds and moves cash and distributes notes to other agents.
    """
    def __init__(self, initial_balance=10_000_000, requester=None):
        super().__init__("Bank", initial_balance, requester=requester)
        self.reserve_requirement = 0.1 # TODO: for a USD bank these are updated by the Fed (central bank)
        self.prime_rate = random.uniform(0.01, 0.1) 
        self.reserve = 0
        self.aum = initial_balance #TODO: will be set of loans from the Fed (central bank)
        self.assets = []
        self.deposits = []
        self.loans = []
        self.accounts = []
        self.credit = []
        self.current_date = datetime(1700,1,1)
        
    async def open_savings_account(self, agent, initial_balance=0):
        """
        Creates a savings account for an agent with a randomly changing interest rate.
        """
        found_account = (await self.get_savings_account(agent))
        if found_account != None:
            return {"savings": found_account, "note": "Account already exists."}
        account = SavingsAccount(agent, initial_balance, self.prime_rate)
        self.accounts.append(account)
        return {"savings": account.to_dict()}

    async def get_savings_account(self, agent):
        """
        Gets an agent's savings account.
        """
        for account in self.accounts:
            if account.owner == agent:
                return {"savings": account.to_dict()}
        return None
    
    async def deposit_savings(self, agent, amount):
        """
        Deposits an amount into the agent's savings account.
        """
        for account in self.accounts:
            if account.owner == agent:
                await account.deposit(amount)
                self.deposits.append(amount)
                return account.to_dict()
        print("Account not found.")
        return None
    
    async def withdraw_savings(self, agent, amount, to):
        """
        Withdraws an amount from the agent's savings account.
        """
        for account in self.accounts:
            if account.owner == agent:
                if amount > account.balance:
                    return {"withdraw":"Insufficient funds."}
                await account.withdraw(amount)
                return {"withdraw": amount}
        return {"withdraw": "Account not found."}
    
    async def get_savings_balance(self, agent):
        """
        Gets an agent's savings account balance.
        """
        for account in self.accounts:
            if account.owner == agent:
                return {"balance": account.balance}
        return None
    
    async def set_credit(self, agent, amount):
        """
        Sets an agent's credit score.
        """
        found_credit = (await self.get_credit(agent))
        if found_credit != None:
             credit[found_credit["index"]].score = amount
        else :
            credit = Credit(agent, 300)
            self.credit.append(credit)
        

    async def get_credit(self, agent):
        """
        Gets an agent's credit score.
        """
        for index, credit in enumerate(self.credit):
            if credit.agent == agent:
                return {"credit": credit.to_dict(), "index": index}
        return None

    def calculate_credit_factor(self, credit_score, rate_type="fixed"):
        """
        Calculate the loan's additional interest rate based on the borrower's credit score.
        """
        if rate_type == "variable":
            credit_factor = 1.0 - (credit_score / 1000.0) * .01
        if rate_type == "fixed":
            credit_factor = 1.0 - (credit_score / 1000.0) * .015
        return credit_factor

    async def apply_for_loan(self, agent, rate_type="fixed"):
        """
        Applies for a loan.
        """
        found_credit = (await self.get_credit(agent))
        found_savings = await self.get_savings_account(agent)
        if found_credit == None:
            return {"loan": "Denied, Agent has no credit score."}
        if found_credit["credit"]["score"] <= 300:
            return {"loan": "Denied, Agent has poor credit score."}
        if found_savings == None:
            return {"loan": "Denied, Agent has no savings account."}
        # if found_savings["savings"]["balance"] <= 0:
        #     return {"loan": "Denied, Agent has insufficient funds."}
        
        if found_credit["credit"]["score"] > 300 and found_credit["credit"]["score"] < 400:
            amount = 1000
           
        if found_credit["credit"]["score"] >= 400 and found_credit["credit"]["score"] < 500:
            amount = 5000
            
        if found_credit["credit"]["score"] >= 500 and found_credit["credit"]["score"] < 600:
            amount = 10000

        if found_credit["credit"]["score"] >= 600 and found_credit["credit"]["score"] < 700:
            amount = 50000

        if found_credit["credit"]["score"] >= 700 and found_credit["credit"]["score"] < 800:
            amount = 100000

        factored_rate = self.calculate_credit_factor(found_credit["credit"]["score"])
        return await self.issue_loan(agent, amount, factored_rate, rate_type)
            

    async def issue_loan(self, borrower, amount, factored_rate=random.uniform(0.01, 0.05), rate_type="fixed"):
        """
        Issues a loan to the borrower.
        """
        if (await self.get_savings_account(borrower)) == None:
            return {"loan": "Denied, Borrower has no savings account."}
        loan = Loan(borrower, amount, factored_rate+self.prime_rate, rate_type)
        self.loans.append(loan)
        self.reserve -= amount
        return {"loan": amount}
       
    async def update_prime_rate(self, new_rate=random.uniform(0.01, 0.1)):
        """
        Update the interest rate with a random change.
        """
        # TODO: for a USD bank this would be updated by the interest rates of loans taken from the Fed (central bank)
        self.prime_rate = new_rate

    async def next(self):
        """
        Perform actions in the next time step.
        """
        if self.current_date.day == 1:
            await self.update_prime_rate()

        for account in self.accounts:
            if self.current_date.day == 1:
                await account.update_balance()
                account.interest_rate = self.prime_rate
            await account.compound_interest()

            for loan in self.loans:
                if loan.amount == 0:
                    self.loans.remove(loan)
                if self.current_date.day == 1:
                    amount = (await loan.deduct_payment(account))
                    repayment_factor = amount / loan.amount
                    pre_payment_credit = await self.get_credit(loan.borrower)["credit"]["score"]
                    updated_score = pre_payment_credit + int(repayment_factor * 10)
                    await self.set_credit(loan.borrower,)
                    if loan.rate_type == "variable":
                        current_credit =await self.get_credit(loan.borrower)["credit"]["score"]
                        loan.interest_rate = self.calculate_credit_factor(current_credit, loan.rate_type)+self.prime_rate

                await loan.accrue_interest()

class Credit:
    """
    Represents an agent's credit score.
    """
    def __init__(self, agent, score):
        self.agent = agent
        self.score = score

    def to_dict(self):
        """
        Get a dictionary representation of the credit score.
        """
        return {
            "agent": self.agent,
            "score": self.score
        }

class SavingsAccount:
    """
    Represents a savings account with an interest rate changing according to a prime rate.
    """

    def __init__(self, owner, initial_balance=0, initial_interest_rate=0.01):
        self.owner = owner
        self.balance = initial_balance
        self.interest_rate = initial_interest_rate
        self.accrued_interest = 0

    async def compound_interest(self):
        """
        Compounds the interest on the account's balance.
        """
        daily_interest = self.balance * self.interest_rate / 365
        self.accrued_interest += daily_interest

    async def update_balance(self):
        """
        Add the accrued interest to the balance.
        """
        self.balance += self.accrued_interest
        self.accrued_interest = 0

    async def deposit(self, amount):
        """
        Deposit funds into the account.
        """
        self.balance += amount

    async def withdraw(self, amount):
        """
        Withdraw funds from the account if there are sufficient funds.
        """
        if amount <= self.balance:
            self.balance -= amount
        else:
            print("Insufficient funds.")

    async def get_balance(self):
        """
        Get the current balance of the account.
        """
        return self.balance
    
    def to_dict(self):
        """
        Get a dictionary representation of the account.
        """
        return {
            "owner": self.owner,
            "balance": self.balance,
            "interest_rate": self.interest_rate,
            "accrued_interest": self.accrued_interest
        }

class Loan:
    """
    Represents a loan with daily accrued interest.
    """
    def __init__(self, borrower, amount, interest_rate=random.uniform(0.05, 0.15), rate_type="fixed"):
        self.borrower = borrower
        self.principal = amount
        self.amount = amount # current remaining principal + interest
        self.rate_type = rate_type
        self.interest_rate = interest_rate
        self.interest_accrued = 0

    async def accrue_interest(self):
        """
        Accrue daily interest on the loan.
        """
        daily_interest = self.amount * self.interest_rate / 365
        self.interest_accrued += daily_interest
        self.amount += daily_interest

    async def deduct_payment(self, account, amount=0):
        """
        Deduct a portion of the loan's principle and accrued interest from the borrower's savings account.
        """
        minimum_payment = self.amount * 0.1
        if amount == "minimum" or amount < minimum_payment: payment = minimum_payment
        elif amount > minimum_payment: payment = amount
        elif amount > self.amount: payment = self.amount
        if payment > (await account.get_balance()):
            print("Loan payment failed due to insufficient funds.")
        if payment <= (await account.get_balance()):
                await account.withdraw(payment)
                self.amount -= payment

        return amount
