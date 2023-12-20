import os, sys
file_dir = os.path.dirname(os.path.abspath(__file__))
source_dir = os.path.dirname(file_dir)
parent_dir = os.path.dirname(source_dir)
sys.path.append(parent_dir)
from source.Messaging import Publisher
from source.Clock import Clock
from multiprocessing import Process
from time import sleep

def run_clock() -> None:
    try:
        p = Publisher(5114)
        clock = Clock()
        while True:
            clock.tick()
            msg = p.publish("time", str(clock.dt))
            sleep(.001)
    
    except KeyboardInterrupt:
        print("attempting to close clock..." )
        return
    
def main() -> None:
    try:
        clock_process = Process(target=run_clock)

        clock_process.start()

        while True:
            sleep(.1)

    except KeyboardInterrupt:
        print("attempting to close processes..." )
        clock_process.terminate()
        clock_process.join()

if __name__ == '__main__':
    main()