class ConstantProduct:
    def __init__(self, reserve_a, reserve_b):
        self.reserve_a = reserve_a
        self.reserve_b = reserve_b
        self.k = reserve_a * reserve_b

    def get_price(self, delta_a):
        """
        Returns the price of token_b of the pool given a delta_a
        
        delta_a: the amount of token_a or `base`
        delta_b: the amount of token_b or `quote`
        """
        new_reserve_a = self.reserve_a + delta_a
        new_reserve_b = self.k / new_reserve_a
        delta_b = self.reserve_b - new_reserve_b
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
        self.k = self.reserve_a * self.reserve_b
        return delta_b
    
    def get_total_reserves(self):
        """
        Returns the total reserves of the pool

        `NOTE: only useful for comparing pools of the same pair with different fees`
        """
        return self.reserve_a + self.reserve_b
    
    def to_dict(self):
        return {
            'reserve_a': self.reserve_a,
            'reserve_b': self.reserve_b,
            'k': self.k,
        }
    