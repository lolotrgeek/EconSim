import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
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