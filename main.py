import subprocess
from time import sleep
from signal import SIGTERM
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__name__)))

files = [
    parent_dir+'\\EconSim\\run_crypto_exchange.py',
    parent_dir+'\\EconSim\\run_crypto.py',
    parent_dir+'\\EconSim\\run_government.py',
    parent_dir+'\\EconSim\\run_clock.py',
]
traders = [
    parent_dir+'\\EconSim\\run_trader_maker.py',
    parent_dir+'\\EconSim\\run_trader_taker.py',
]
api = [
    parent_dir+'\\EconSim\\source\\api\crypto_exchange_api.js',
    parent_dir+'\\EconSim\\source\\api\government_api.js',
    parent_dir+'\\EconSim\\source\\api\crypto_api.js',
]


if __name__ == '__main__':
    try:
        # Clear log files
        # logs_dir = parent_dir+'\\EconSim\\logs'
        # for file in os.listdir(logs_dir):
        #     if file.endswith(".log"):
        #         os.remove(os.path.join(logs_dir, file))

        #Start processes
        processes = []
        for file in files:
            process = subprocess.Popen(['python', file])
            processes.append(process)
            sleep(.1)

        for file in api:
            process = subprocess.Popen(['node', file])
            processes.append(process)

        sleep(5)

        for trader in traders:
            process = subprocess.Popen(['python', trader])
            processes.append(process)
            sleep(.1)

        while True:
            sleep(.1)
    except KeyboardInterrupt:
        print("attempting to close economy..." )
        for process in processes:
            process.send_signal(SIGTERM)
        exit()

