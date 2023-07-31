from source.Energy import Energy
from datetime import datetime

class Run():
    def __init__(self):
        self.energy = Energy()
        
    async def next(self, runner):
        while self.energy.available_energy > 0:
            start_time = datetime.now()
            await runner(self.energy)
            end_time = datetime.now()
            run_time = (end_time - start_time).total_seconds()
            self.energy.energyUsed(run_time)
            
