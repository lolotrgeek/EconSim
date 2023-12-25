import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(parent_dir)
from source.utils._utils import prec, non_zero_prec

class ConstantProduct:
    def __init__(self, reserve_a, reserve_b):
        self.reserve_a = reserve_a
        self.reserve_b = reserve_b
        self.k = prec(reserve_a * reserve_b)

    def get_price(self, delta_a):
        """
        Returns the price of token_b of the pool given a delta_a
        
        delta_a: the amount of token_a or `base`
        delta_b: the amount of token_b or `quote`
        """
        new_reserve_a = prec(self.reserve_a + delta_a)
        new_reserve_b = prec(self.k / new_reserve_a)
        delta_b = prec(self.reserve_b - new_reserve_b)
        return delta_b

    def balance(self,delta_a):
        """
        Balances the pool

        delta_a: the amount of token_a or `base`
        delta_b: the amount of token_b or `quote`
        """
        delta_b = self.get_price(delta_a)
        self.reserve_a += delta_a
        self.reserve_b -= delta_b
        self.k = non_zero_prec(self.reserve_a * self.reserve_b)
        return delta_b
    
    def get_total_reserves(self):
        """
        Returns the total reserves of the pool

        `NOTE: only useful for comparing pools of the same pair with different fees`
        """
        return prec(self.reserve_a + self.reserve_b)
    
    def to_dict(self):
        return {
            'reserve_a': self.reserve_a,
            'reserve_b': self.reserve_b,
            'k': self.k,
        }
    