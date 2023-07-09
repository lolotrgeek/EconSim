from .utils._utils import get_datetime_range, get_timedelta
from datetime import datetime, timedelta

class Clock():
    def __init__(self, dt=datetime(1700,1,1), time_unit='minute') -> None:
        #NOTE: we are choosing the 1700 as year because it is the furthest year that pandas will resample
        self.dt = dt
        self.timeDelta = get_timedelta(time_unit)
        
    def tick(self):
        self.dt +=self.timeDelta
        return self.dt
