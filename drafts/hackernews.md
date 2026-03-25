**Title:** Show HN: HotBunk — Load-balance Claude Code across multiple Max accounts

**URL:** https://github.com/drewbeyersdorf/hotbunk

**Comment (if posting as Show HN):**

Claude Max subscriptions are $100-200/month for rate-limited "unlimited" usage. The equivalent API tokens for the same throughput would cost $5K-30K/month. The arbitrage is real — but the bottleneck is rate limits per account.

If you're running multiple machines or automated agents, you're burning through one account's limits while others sit idle. HotBunk pools multiple accounts and routes automated workloads to whoever has headroom.

Consent model: each account owner sets a YAML policy controlling what job types, hours, and concurrency are allowed. Interactive sessions always take priority over automation.

Named after submarine hot bunking — 130 sailors, 60 bunks, crews share beds across watch shifts.

Early stage. Python CLI. Works on Linux. Looking for feedback from anyone else running multi-account Claude Code setups.
