**Title:** I built a tool that load-balances Claude Code across multiple Max accounts

**Body:**

The math on Max accounts is wild. $200/month for a Max 5x subscription gives you more Opus throughput than $5,000+ in API tokens. The arbitrage is 30-50x depending on how hard you push it.

The problem is rate limits. One account hits the ceiling, you wait. Meanwhile your other account — or your teammate's account — is sitting there doing nothing.

I'm running 4 machines with Claude Code (dev workstation, ML rig, two always-on boxes running automated agents). Two Max accounts. Kept hitting limits on one while the other was dark.

So I built HotBunk. It pools multiple Max accounts and routes automated workloads to whoever has headroom. Interactive sessions always take priority — if you sit down at your machine, your account is yours. Automation only runs on idle capacity.

The name comes from submarine hot bunking — crews share the same bunks across shifts because there aren't enough beds for everyone. Same idea with rate limits.

Each account owner sets a policy (YAML) controlling exactly what can run on their account and when. Sleep windows, job types, concurrency caps. Nothing runs without explicit opt-in.

What it does right now:

```
hotbunk status          # see all accounts and headroom
hotbunk switch personal # swap active account
hotbunk submit militia -c "claude -p 'run audit'"  # route job to idle account
hotbunk monitor         # live TUI dashboard
```

Still early. V1 works across my own 2 accounts. Building toward multi-machine orchestration with a daemon and web dashboard.

Open source, MIT: https://github.com/drewbeyersdorf/hotbunk

Curious if anyone else is running into the same rate limit juggling problem with multiple accounts.
