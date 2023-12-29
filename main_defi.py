import subprocess
from time import sleep
from signal import SIGTERM
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__name__)))

files = [
    parent_dir+'\\EconSim\\source\\runners\\run_defi_exchange.py',
    parent_dir+'\\EconSim\\source\\runners\\run_crypto.py',
    parent_dir+'\\EconSim\\source\\runners\\run_clock.py',
]
traders = [
    parent_dir+'\\EconSim\\source\\runners\\run_trader_defi.py',
    # parent_dir+'\\EconSim\\run_trader_maker.py',
    # parent_dir+'\\EconSim\\run_trader_taker.py',
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

