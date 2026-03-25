# hotbunk

Cooperative compute orchestrator for Claude Code. Share idle capacity across Max accounts without sharing credentials.

## What it does

Multiple people each bring their own Claude Max account. Everyone uses their account normally. When someone isn't in an active session, their idle capacity is available for shared automated workloads -- agents, training pipelines, CI jobs.

Every account owner explicitly opts in and controls what their account can be used for and when.

## How it works

```
hotbunk status          # see all accounts and their current state
hotbunk submit          # submit an automated job to the pool
hotbunk policy --edit   # control what your account is used for
hotbunk dashboard       # open the web dashboard
```

Accounts have four states:
- **Interactive** -- owner is active, automation stays away
- **Idle** -- no active session, pool can use spare capacity
- **Sleeping** -- in declared sleep window, full automation access
- **Throttled** -- rate limited, recovering

Interactive sessions always have priority. Automated workloads are scavengers that only use idle capacity.

## Why "hot bunk"

On submarines, crews share the same bunks across shifts -- there aren't enough beds for everyone at once. HotBunk does the same thing with Claude Code rate limits. Your account sleeps in someone else's machine when you're not using it.

## Status

Early development. V1 targets 2 accounts across 4 machines.

## License

MIT
