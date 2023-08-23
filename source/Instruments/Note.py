# base class for various notes

from random import random
from datetime import datetime, timedelta
import uuid
class Note():
    """The Note class is the base class for developing different notes that are issued by the government, banks or companies.
    """
    def __init__(self, face_value, maturity_years):
        self.face_value = face_value
        self.maturity_years = maturity_years
        self.maturity_date = None
        self.interest_rate = None
        self.interest_payment = None
        self.principal_payment = None
        self.total_payment = None
        self.id = uuid.uuid4()
        self.owner = None

    def __repr__(self):
        return f'<Note: {self.id}>'

    def __str__(self):
        return
    
    def generate_maturity_date(self, issue_date):
        """Generates the maturity date of the note.

        Args:
            issue_date (datetime): the date the note was issued.
        """
        self.maturity_date = issue_date + timedelta(days=(365 * self.maturity_years))


class TreasuryNote(Note):
    """The TreasuryNote class is a subclass of the Note class that represents a treasury note issued by the government.
    """
    def __init__(self, face_value, maturity_years):
        super().__init__(face_value, maturity_years)
        self.coupon_rate = None
        self.yield_to_maturity = None

    def __repr__(self):
        return f'<TreasuryNote: {self.id}>'

    def __str__(self):
        return f'<TreasuryNote: {self.id}>'

    def generate_coupon_rate(self):
        """Generates a random coupon rate for the note.
        """
        self.coupon_rate = random.uniform(0.0, 0.05)

    def generate_yield_to_maturity(self):
        """Generates a random yield to maturity for the note.
        """
        self.yield_to_maturity = random.uniform(0.0, 0.05)

    def generate_note_info(self):
        """Generates a random coupon rate and yield to maturity for the note.
        """
        self.generate_coupon_rate()
        self.generate_yield_to_maturity()
    

class Bond(Note):
    """The Bond class is a subclass of the Note class that represents a bond issued by a company.
    """
    def __init__(self, face_value, maturity_years):
        super().__init__(face_value, maturity_years)
        self.coupon_rate = None
        self.yield_to_maturity = None

    def __repr__(self):
        return f'<Bond: {self.id}>'

    def __str__(self):
        return f'<Bond: {self.id}>'

    def generate_coupon_rate(self):
        """Generates a random coupon rate for the bond.
        """
        self.coupon_rate = random.uniform(0.0, 0.05)

    def generate_yield_to_maturity(self):
        """Generates a random yield to maturity for the bond.
        """
        self.yield_to_maturity = random.uniform(0.0, 0.05)

    def generate_bond_info(self):
        """Generates a random coupon rate and yield to maturity for the bond.
        """
        self.generate_coupon_rate()
        self.generate_yield_to_maturity()


class Loan(Note):
    """The Loan class is a subclass of the Note class that represents a loan issued by a bank.
    """
    def __init__(self, face_value, maturity_years):
        super().__init__(face_value, maturity_years)
        self.interest_rate = None

    def __repr__(self):
        return f'<Loan: {self.id}>'

    def __str__(self):
        return f'<Loan: {self.id}>'

    def generate_interest_rate(self):
        """Generates a random interest rate for the loan.
        """
        self.interest_rate = random.uniform(0.0, 0.05)

    def generate_loan_info(self):
        """Generates a random interest rate for the loan.
        """
        self.generate_interest_rate()

        