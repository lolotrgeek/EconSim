import subprocess
from time import sleep
from signal import SIGTERM
import sys
import os
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
file = parent_dir+'\\EconSim\\run_agent.py'
print(file)

if __name__ == '__main__':
    try:
        num_agents = 20
        agents = []

        for i in range(num_agents):
            agent = subprocess.Popen(['python', file, '5570'])
            print(f"Agent {i} connected")
            agents.append(agent)

        while True:
            sleep(.1)
    except KeyboardInterrupt:
        print("attempting to close agents..." )
        for agent in agents:
            agent.send_signal(SIGTERM)
        exit()

