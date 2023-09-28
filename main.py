import subprocess
from time import sleep
from signal import SIGTERM
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
files = [
    parent_dir+'\\EconSim\\run_crypto_exchange.py',
    parent_dir+'\\EconSim\\run_crypto.py',
    parent_dir+'\\EconSim\\run_government.py',
    parent_dir+'\\EconSim\\run_clock.py',
    parent_dir+'\\EconSim\\run_traders.py',
]
api = [
    parent_dir+'\\EconSim\\source\\api\crypto_exchange_api.js',
    parent_dir+'\\EconSim\\source\\api\government_api.js',
    parent_dir+'\\EconSim\\source\\api\crypto_api.js',
]


if __name__ == '__main__':
    try:
        processes = []
        for file in files:
            process = subprocess.Popen(['python', file])
            processes.append(process)
            sleep(.1)

        for file in api:
            process = subprocess.Popen(['node', file])
            processes.append(process)

        while True:
            sleep(.1)
    except KeyboardInterrupt:
        print("attempting to close economy..." )
        for process in processes:
            process.send_signal(SIGTERM)
        exit()

