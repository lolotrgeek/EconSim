# 🚀qmrExchange - Process🚀
A simulated exchange where price action is a result of agents interacting through an order book.

This implements qmrExchange where agents and the exchange run in separate processes.

## UNDER DEVELOPMENT
-- version 0.1 -- 

## Usage

```
python main.py
```

Add agent to `Agents.py` extending `Agent` class from `AgentProcess`, then import the Agent into `run.py` -> `def run_agent():` to multiprocess or run in separate process manually.

## Adding Features

Add function to `Exchange` then update `Request` and `Agent` then add corresponding responses in `run.py` -> `def run_exchange():`

To Test add the response from `run.py` into `MockRequester` and add tests for new feature to `test_Requests` , `test_Agent` , `test_Exchange`

