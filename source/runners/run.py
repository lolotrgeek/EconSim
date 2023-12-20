import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
from source.Energy import Energy
from datetime import datetime

class Run():
    def __init__(self):
        self.energy = Energy()
        
    async def next(self, runner) -> None:
        while self.energy.available_energy > 0:
            start_time = datetime.now()
            await runner(self.energy)
            end_time = datetime.now()
            run_time = (end_time - start_time).total_seconds()
            self.energy.energyUsed(run_time)
            
