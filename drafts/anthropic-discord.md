**Channel:** #claude-code (or #show-and-tell if available)

**Message:**

Built an open source tool for load-balancing Claude Code across multiple Max accounts.

The problem: running 4 machines with automated agents, two Max accounts. One hits rate limits while the other sits idle.

HotBunk pools the accounts and routes automated workloads to whoever has headroom. Interactive sessions always take priority. Each account owner sets a consent policy (YAML) for what's allowed on their account.

```
hotbunk status     # see all accounts
hotbunk submit militia -c "claude -p 'run task'"
hotbunk monitor    # live TUI
```

Python, MIT, Linux. Early stage.

GitHub: https://github.com/drewbeyersdorf/hotbunk
Site: https://hotbunk.dev
