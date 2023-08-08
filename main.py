import subprocess
from time import sleep
from signal import SIGTERM
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = [
    parent_dir+'\\EconSim\\run_exchange.py',
    parent_dir+'\\EconSim\\run_agents.py',
    parent_dir+'\\EconSim\\run_government.py',
    parent_dir+'\\EconSim\\run_clock.py',
]
api = [
    parent_dir+'\\EconSim\\source\\api\exchange_api.js',
    parent_dir+'\\EconSim\\source\\api\government_api.js'
]


if __name__ == '__main__':
    try:
        processes = []
        for file in files:
            process = subprocess.Popen(['python', file])
            processes.append(process)

        for file in api:
            process = subprocess.Popen(['node', file])
            processes.append(process)

        while True:
            sleep(.1)
    except KeyboardInterrupt:
        print("attempting to close agents..." )
        for process in processes:
            process.send_signal(SIGTERM)
        exit()

