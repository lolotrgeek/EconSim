import subprocess
from time import sleep
from signal import SIGTERM
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = [
    parent_dir+'\\EconSim\\run_exchange.py',
    parent_dir+'\\EconSim\\run_traders.py',
    parent_dir+'\\EconSim\\run_government.py',
    parent_dir+'\\EconSim\\run_clock.py',
]


if __name__ == '__main__':
    try:
        processes = []
        for file in files:
            process = subprocess.Popen(['python', file])
            processes.append(process)

        while True:
            sleep(.1)
    except KeyboardInterrupt:
        print("attempting to close economy..." )
        for process in processes:
            process.send_signal(SIGTERM)
        exit()

