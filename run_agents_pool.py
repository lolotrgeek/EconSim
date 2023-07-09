import multiprocessing
import asyncio
from run_agent import run_agent
import traceback
if __name__ == '__main__':
    try:
        print('starting agents')
        pool = multiprocessing.Pool(processes=500)
        results = []
        for _ in range(500):
            result = pool.apply_async(asyncio.run, args=(run_agent(),))
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