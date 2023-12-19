import os, sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import multiprocessing
import asyncio
from .run_trader import run_trader
import traceback
if __name__ == '__main__':
    try:
        print('starting traders')
        pool = multiprocessing.Pool(processes=500)
        results = []
        for _ in range(500):
            result = pool.apply_async(asyncio.run, args=(run_trader(),))
            results.append(result)
        
        pool.close()
        pool.join()
        
        for result in results:
            if result.get() is None:
                print('Agent execution failed')
        
    except Exception as e:
        print("[Agent Error] ", e)
        traceback.print_exc()
        exit()