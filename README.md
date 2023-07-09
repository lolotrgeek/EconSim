# 🚀EconSim🚀
A simulated economy with an exchange using backed assets.

## UNDER DEVELOPMENT
-- version 0.1 -- 

## Usage

```
python run_clock.py
python run_exchange.py
python run_agents.py

```

Run dashboard
```
cd source/app/dashboard
npm run start
```

Add agent to `Agents.py` extending `Agent` class from `AgentProcess`, then import the Agent into `run.py` -> `def run_agent():` to multiprocess or run in separate process manually.

## Adding Features

Add function to `Exchange` then update `Request` and `Agent` then add corresponding responses in `run.py` -> `def run_exchange():`

To Test add the response from `run.py` into `MockRequester` and add tests for new feature to `test_Requests` , `test_Agent` , `test_Exchange`

## Test
```
pytest
```


## Asset Backing

## Credits
Exchange based on https://github.com/QMResearch/qmrExchange 