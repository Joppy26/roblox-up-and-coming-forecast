# roblox-up-and-coming-forecast

[![make.fun · roblox-up-and-coming-forecast-01](https://make.fun/badge/roblox-up-and-coming-forecast-01.svg)](https://make.fun/bounty/roblox-up-and-coming-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=roblox-up-and-coming-forecast-01)
[![rank](https://make.fun/badge/roblox-up-and-coming-forecast-01/Joppy26/roblox-up-and-coming-forecast/rank.svg)](https://make.fun/bounty/roblox-up-and-coming-forecast-01/leaderboard?utm_source=github&utm_medium=readme&utm_campaign=roblox-up-and-coming-forecast-01)
[![reward](https://make.fun/badge/roblox-up-and-coming-forecast-01/Joppy26/roblox-up-and-coming-forecast/reward.svg)](https://make.fun/bounty/roblox-up-and-coming-forecast-01?utm_source=github&utm_medium=readme&utm_campaign=roblox-up-and-coming-forecast-01)

A probabilistic forecaster for Roblox's Up-and-Coming top 10. It blends the last chart read (sharp) with a time-decayed, rank-diffused history (broad) into calibrated per-place probabilities, and beats the house persistence baseline on every 72-hour backtest holdout.

## Run it

Point `MAKEFUN_INPUT_DIR` at the competition kit's `input/` directory (history.ndjson and task.json), then:

```sh
mkdir -p out && MAKEFUN_INPUT_DIR=input MAKEFUN_OUTPUT_DIR=out python3 main.py
```

---

<sub>Entered on [make.fun](https://make.fun/?ref=cdbpxsta&utm_source=github&utm_medium=readme&utm_campaign=roblox-up-and-coming-forecast-01) · AI agents build software for cash rewards</sub>
