from run import Run
from time import sleep
from random import randint
import traceback
import asyncio
asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())


async def runner(energy):
    costPerkWh = 0.15
    total_cost = energy.energyCost(energy.totalenergyUsed)
    print(f"available energy: {energy.available_energy}, total energy used: {energy.totalenergyUsed}, energy used last run: {energy.energyUsedlastRun} kWh, total cost: ${total_cost}")
    sleep(randint(1,5))
    

async def run_test():
    run = Run()
    run.energy.available_energy = 100
    await run.next(runner)
    print("done")

if __name__ == '__main__':
    try:
        asyncio.run(run_test())
    except Exception as e:
        print("[Run Test Error] ", e)
        traceback.print_exc()
        exit()