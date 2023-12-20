import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from source.Clock import Clock

async def get_time() -> None:
    clock = Clock()
    clock.tick()
    return clock.dt
