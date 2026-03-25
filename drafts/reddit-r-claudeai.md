**Title:** I built a tool that load-balances Claude Code across multiple Max accounts

**Body:**

$200/month for Max 5x. The equivalent API tokens for the same Opus throughput would run $5,000-30,000. That's a 30-50x arbitrage.

The bottleneck is rate limits. Hit the ceiling on one account, you wait. Meanwhile your second account is doing nothing. Eight hours of sleep is eight hours of premium compute sitting dark.

I'm running 4 machines with Claude Code — dev workstation, ML rig, two always-on boxes running automated agents. Two Max accounts. Kept hitting limits on one while the other had full headroom.

So I built HotBunk. Pools multiple Max accounts and routes automated workloads to whoever has capacity. Interactive sessions always take priority — you sit down, your account is yours. Automation is the scavenger. It only touches idle capacity.

The name comes from submarine hot bunking. 130 sailors, 60 bunks. Crews share the same beds across watch shifts. The bunk is always warm.

Each account owner sets a consent policy (YAML) — what job types are allowed, sleep windows, concurrency caps. Nothing runs without explicit opt-in.

```
hotbunk status          # see all accounts and headroom
hotbunk switch personal # swap active account
hotbunk submit militia -c "claude -p 'run audit'"  # route job to idle account
hotbunk monitor         # live TUI dashboard
```

Still early. V1 works across my 2 accounts. Building toward multi-machine orchestration with a daemon and web dashboard.

Open source, MIT: https://github.com/drewbeyersdorf/hotbunk

Site: https://hotbunk.dev
