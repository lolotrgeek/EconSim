class ConstantProduct:
    def __init__(self, reserve_a, reserve_b):
        self.reserve_a = reserve_a
        self.reserve_b = reserve_b
        self.k = reserve_a * reserve_b

    def get_price(self, delta_a):
        new_reserve_a = self.reserve_a + delta_a
        new_reserve_b = self.k / new_reserve_a
        delta_b = self.reserve_b - new_reserve_b
        return delta_b

    def balance(self,delta_a):
        delta_b = self.get_price(delta_a)
        self.reserve_a += delta_a
        self.reserve_b -= delta_b
        self.k = self.reserve_a * self.reserve_b
        return delta_b
    
    def get_total_reserves(self):
        return self.reserve_a + self.reserve_b
    
    def to_dict(self):
        return {
            'reserve_a': self.reserve_a,
            'reserve_b': self.reserve_b,
            'k': self.k,
        }
    