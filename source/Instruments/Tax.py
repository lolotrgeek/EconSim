class Tax():
    def __init__(self):
        self.brackets = {
            "ordinary": [
                {"rate": 0.1, "min": 0, "max": 22000},
                {"rate": 0.12, "min": 22001, "max": 89450},
                {"rate": 0.22, "min": 89451, "max": 190750},
                {"rate": 0.24, "min": 190751, "max": 364200},
                {"rate": 0.32, "min": 364201, "max": 462500},
                {"rate": 0.35, "min": 462501, "max": 693750},
                {"rate": 0.37, "min": 693751}
            ],
            "long_term": [
                {"rate": 0, "min": 0, "max": 83350},
                {"rate": 0.15, "min": 83351, "max": 517200},
                {"rate": 0.20, "min": 517201}
            ],
            "state": [ 
                { "rate": 0.00, "min": 0, "max": 111 }, 
                { "rate": 0.015, "min": 112, "max": 1121 }, 
                { "rate": 0.020, "min": 1122, "max": 2242 }, 
                { "rate": 0.025, "min": 2243, "max": 3363 }, 
                { "rate": 0.030, "min": 3364, "max": 4484 },
                { "rate": 0.035, "min": 4485, "max": 5605 },
                { "rate": 0.040, "min": 5606, "max": 6726 },
                { "rate": 0.045, "min": 6727, "max": 7847 },
                { "rate": 0.050, "min": 7848, "max": 8968 }, 
                { "rate": 0.053, "min": 8969 }                
            ]
        }
        
    async def calculate_tax(self, income, bracket_type, debug=False) -> dict:
        tax = 0
        income_left = income
        bracket_index = 0
        income_rates = []
        
        while income_left > 0:
            bracket = self.brackets[bracket_type][bracket_index]
            if debug:
                print(bracket)
            
            if 'max' not in bracket:
                tax += income_left * bracket['rate']
                income_left = 0
                income_rates.append({'income': income_left, 'rate': bracket['rate']})
                break
            
            else:
                income_in_bracket = min(income_left, bracket['max'] - bracket['min'])
                tax += income_in_bracket * bracket['rate']
                income_left -= income_in_bracket
                if debug:
                    print(f"rate: {bracket['rate']} {income_left} tax: {tax}")
                income_rates.append({'income': income_in_bracket, 'rate': bracket['rate']})
                
                if income_left == 0:
                    break
                
                if bracket_index < len(self.brackets[bracket_type]) - 1:
                    bracket_index += 1
        
        marginal_rate = self.brackets[bracket_type][bracket_index]['rate']
        
        return {'amount': tax, 'marginalRate': marginal_rate, 'income_rates': income_rates}
    