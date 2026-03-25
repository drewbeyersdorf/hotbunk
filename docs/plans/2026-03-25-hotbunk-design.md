# HotBunk - Cooperative Compute Orchestrator for Claude Code

**Date:** 2026-03-25
**Status:** Approved
**Author:** Drew B.

## Problem

Claude Max accounts provide 10-50x more value per dollar than API tokens, but each account has rate limits. When running multiple machines (4+) with heavy workloads (development, automation, training), a single account hits limits regularly. Multiple accounts solve this, but there's no tool to coordinate usage across accounts and machines.

## Solution

HotBunk is a cooperative compute pool for Claude Code. N people each bring their own Max account. Each person uses their account normally for interactive work. When someone isn't actively using their account, their idle capacity is available for shared automated workloads -- militia agents, training pipelines, CI jobs.

Every account owner explicitly opts in and defines what their account can be used for and when.

## Core Concepts

### Account Policy (set by each owner)

Each account owner defines their policy:

```yaml
owner: drew
email: drew@example.com
interactive_priority: always    # my sessions always take precedence
allow_automated: true           # pool can use my idle capacity
automated_types:                # what job types I allow
  - militia
  - training
  - ci
sleep_window: "22:00-06:00"    # hours I definitely won't be using it
availability: always            # always | workdays | weekdays | custom
max_automated_concurrent: 2     # cap on simultaneous automated jobs
```

### Account States

```
INTERACTIVE  -> owner is in an active session, no automated jobs
IDLE         -> no active session, automated jobs can run (within policy)
SLEEPING     -> in declared sleep window, full automated access
THROTTLED    -> rate limited, no new jobs routed here
COOLDOWN     -> recently throttled, deprioritized for new jobs
```

### Priority Model

1. Interactive sessions always get their own account -- never displaced
2. Automated workloads are scavengers -- only use idle/sleeping accounts
3. When an owner starts an interactive session, automated work yields gracefully
4. If all accounts are hot, automated jobs queue -- they never compete with people

## Architecture

```
                    +-------------------+
                    |   always-on-box (always-on)|
                    |   - orchestrator   |
                    |   - SQLite DB      |
                    |   - dashboard :3000|
                    +--------+----------+
                             |
              Tailscale mesh |
         +-------------------+-------------------+
         |         |                   |          |
    +----+----+  +-+------+  +--------+--+  +----+----+
    |  box-1  |  | box-2  |  |   box-3   |  | box-4   |
    | agent   |  | agent  |  |  agent    |  | agent   |
    +----+----+  +--------+  +-----------+  +---------+
         |
    Owner's interactive
    sessions here
```

### Components

**1. Orchestrator (always-on-box)**
- Python daemon, runs on nerve (always-on M4 Mini)
- SQLite database: accounts, policies, sessions, jobs, usage history
- Polls account usage/rate limit status
- Assigns queued automated jobs to best available account
- REST API for agents and dashboard
- Port: 3000 (dashboard), 3001 (API)

**2. Machine Agent (every machine)**
- Lightweight Python process on each machine
- Reports to orchestrator: active sessions, which account, session start/end
- Watches for new Claude Code processes
- Manages CLAUDE_CONFIG_DIR switching for automated jobs
- Receives job assignments from orchestrator

**3. CLI (hotbunk)**
- `hotbunk status` -- show all accounts, states, headroom
- `hotbunk submit --type militia --command "..."` -- submit automated job
- `hotbunk policy --edit` -- edit your account policy
- `hotbunk switch <account>` -- manual account switch (interactive)
- `hotbunk dashboard` -- open dashboard in browser
- `hotbunk setup` -- first-time credential setup

**4. Dashboard (always-on-box:3000)**
- Simple web UI showing pool status
- All accounts with current state (interactive/idle/sleeping/throttled)
- Active automated jobs and which account they're on
- Usage history and trends
- Accessible from any device on Tailscale

### Credential Management

Each account's credentials are stored in isolated directories:

```
~/.hotbunk/
  accounts/
    user-work/
      .credentials.json    # OAuth tokens
      policy.yaml          # account policy
    user-personal/
      .credentials.json
      policy.yaml
  config.yaml              # orchestrator URL, machine ID
  hotbunk.db               # local cache (synced from always-on-box)
```

Automated jobs launch with `CLAUDE_CONFIG_DIR=~/.hotbunk/accounts/<account>/` to use the correct credentials.

### Consent Ledger

Every policy change and automated job assignment is logged:

```sql
CREATE TABLE consent_log (
  id INTEGER PRIMARY KEY,
  account_id TEXT NOT NULL,
  action TEXT NOT NULL,        -- policy_update, job_assigned, job_completed, access_revoked
  details JSON,
  timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

Any owner can see exactly what ran on their account and when. Any owner can revoke automated access instantly via `hotbunk policy --revoke`.

## Tech Stack

- **Language:** Python 3.12+
- **CLI:** Click
- **Database:** SQLite (via sqlite3, no ORM)
- **API:** FastAPI (orchestrator REST API)
- **Dashboard:** FastAPI + HTMX (simple, no JS framework)
- **Process management:** subprocess + CLAUDE_CONFIG_DIR env var
- **Networking:** Tailscale (already in place)
- **Packaging:** pip installable, single `hotbunk` command

## V1 Scope (2 accounts)

Phase 1 -- 2 accounts, proving the concept:

1. Credential setup for 2 accounts (work + personal)
2. Orchestrator daemon on nerve
3. Machine agent on workstation + always-on-box
4. `hotbunk status` showing both accounts
5. `hotbunk submit` routing automated jobs to idle account
6. Interactive session detection (watch for `claude` processes)
7. Basic dashboard showing pool state
8. Automatic yield when interactive session starts

NOT in V1: multi-user onboarding UI, fancy analytics, mobile app, public API.

## V2 Scope (Team rollout)

- Onboard additional team members
- Per-user dashboard views
- Slack notifications ("your account just picked up a militia batch")
- Usage analytics and reporting
- Rate limit prediction ("account X will recover in ~20 min")

## Success Criteria

- Users can run automated jobs on whichever account has headroom without thinking about it
- Starting an interactive session never fails because automation is hogging the account
- Dashboard shows at a glance which accounts have capacity
- Zero ToS violations -- every account used by its real owner, automation is opt-in overflow
