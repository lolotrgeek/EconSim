import subprocess
from time import sleep
from signal import SIGTERM
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file = parent_dir+'\\EconSim\\run_trader.py'
print(file)

if __name__ == '__main__':
    try:
        num_traders = 12
        traders = []

        for i in range(num_traders):
            trader = subprocess.Popen(['python', file, '5570'])
            print(f"Agent {i} connected")
            traders.append(trader)

        while True:
            sleep(.1)
    except KeyboardInterrupt:
        print("attempting to close traders..." )
        for trader in traders:
            trader.send_signal(SIGTERM)
        exit()

