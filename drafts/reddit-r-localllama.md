**Title:** HotBunk — load-balance Claude Code across multiple Max accounts (open source)

**Body:**

Built this to solve my own problem. Running Claude Code on 4 machines (dev workstation, dedicated ML rig, two always-on boxes for automated agents). Two Max accounts at $200/mo each.

The issue: one account would hit rate limits while the other sat idle. $400/month in subscriptions and half the capacity was dark at any given time.

HotBunk pools the accounts. Automated workloads (agent loops, training data generation, CI) get routed to whichever account has headroom. Interactive sessions always win — automation yields the instant you start a session.

Each account owner sets a consent policy controlling what can run on their account and when. Sleep windows, job types, concurrency caps.

The math that makes this worth it: Max 5x at $200/mo gives you more Opus throughput than $5K-30K in API tokens. Every idle hour on a Max account is burning $15-120 in equivalent API value.

```
hotbunk status     # pool overview
hotbunk submit militia -c "claude -p 'run task'"  # route to best account
hotbunk monitor    # live TUI
```

Python, MIT, early stage: https://github.com/drewbeyersdorf/hotbunk

Works on Linux. macOS support planned. Designed for the multi-machine Claude Code power user setup.
