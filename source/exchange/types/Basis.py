from copy import copy

class Basis():
    def __init__(self, basis_initial_unit, basis_total, basis_txn_id, basis_date):
        """
        Represents the basis of a transaction.
        """
        self.basis_initial_unit = basis_initial_unit
        self.basis_total = basis_total
        self.basis_per_unit = 0
        self.basis_txn_id = basis_txn_id
        self.basis_date = basis_date

    def __repr__(self) -> str:
        return f"Basis({self.basis_initial_unit}, {self.basis_total}, {self.basis_txn_id}, {self.basis_date})"
    
    def __str__(self) -> str:
        return f"<Basis {self.basis_initial_unit} {self.basis_total} {self.basis_txn_id} {self.basis_date}>"
    
    def to_dict(self) -> dict:
        return {
            'basis_initial_unit': self.basis_initial_unit,
            'basis_total': self.basis_total,
            'basis_per_unit': self.basis_per_unit,
            'basis_txn_id': self.basis_txn_id,
            'basis_date': self.basis_date,
        }
    
    def copy(self):
        return copy(self)
    