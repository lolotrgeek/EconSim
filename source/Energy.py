from random import randint

class Energy():
    def __init__(self, available_energy=0):
        self.available_energy = available_energy
        self.totalenergyUsed = 0
        self.maxWatt = 1500
        self.minWatt = 100
        self.powerUsage = 0
        self.energyUsedlastRun = 0

    def energyCost(self, kWh, costPerkWh = 0.15 ):
        return round(costPerkWh * kWh, 10)
    
    def energyUsed(self, run_time):
        '''
        Returns the energy(kWh) used between start_time and end_time
        '''
        usage_floor = round(self.minWatt + (run_time * 100))
        if usage_floor > self.maxWatt: usage_floor = self.maxWatt
        self.poll(usage_floor, self.maxWatt)
        kWh = self.powerUsage * (run_time / 3600)
        self.totalenergyUsed += kWh
        self.available_energy -= kWh
        self.energyUsedlastRun = kWh
        # print(f"Energy used: [{kWh} kWh, ${self.energyCost(kWh)} , {run_time / 3600} hours, {self.powerUsage} kW]")
        return  kWh

    def poll(self, minWatt, maxWatt):
        '''
        Returns a random number of kiloWatts between minWatt and maxWatt
        eventually this will poll an actual power meter
        '''
        self.powerUsage = randint(minWatt, maxWatt) /1000