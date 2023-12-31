# 🚀EconSim🚀
A simulated economy with an exchange using backed assets.

## Goal
Train agents to develop strategies of resource acquisition and allocation via interaction with continuously generative data as opposed to discrete historical data.

## UNDER DEVELOPMENT
-- version 0.2 -- 

- agents trade assets in an exchange
- the trader agents can access financial data generated by the companies each quarter
- a government agent collects taxes from the trader agents based on their PNL

## Next Features
- Banks
- Note issuance, such as Loans and Bonds
- Central Bank to influence money supply
- Public Companies generating finances relative to economics
- Crypto

## Usage

```
python main.py
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

## Credits
Exchange and static agents based on https://github.com/QMResearch/qmrExchange 