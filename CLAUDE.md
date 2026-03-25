# hotbunk

Cooperative compute orchestrator for Claude Code. Multiple people bring their own Claude Max accounts. When someone is not in an active session, their idle capacity is available for shared automated workloads -- agents, training pipelines, CI jobs.

Every account owner explicitly opts in. Interactive sessions always have priority. Automated workloads are scavengers that only use idle capacity.

## Architecture

```
src/hotbunk/
  accounts.py   -- credential storage, switching, consent policies (YAML)
  detector.py   -- watches for active Claude Code processes via /proc
  pool.py       -- routes jobs to the best available account (state machine + scoring)
  cli.py        -- Click CLI: status, register, switch, submit, policy, which, accounts
  monitor.py    -- (planned) background daemon that continuously tracks session state
```

**State machine** (pool.py): each account is in one of five states at any moment:
- INTERACTIVE -- owner is active, automation stays away
- IDLE -- no active session, pool can use spare capacity
- SLEEPING -- in declared sleep window, full automation access
- THROTTLED -- rate limited, recovering
- COOLDOWN -- recently throttled, deprioritized

**Credential isolation**: automated jobs run with `CLAUDE_CONFIG_DIR` set to the account's directory under `~/.hotbunk/accounts/<name>/`. This gives each spawned Claude process its own credential file without touching the owner's `~/.claude/`.

**State storage**: SQLite (planned) for job history and throttle tracking. Currently in-memory only.

**Consent model**: every account has a `policy.yaml` that controls what job types are allowed, concurrency limits, sleep windows, and availability schedules. No automation runs without explicit opt-in.

## Dev Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Testing

```bash
pytest
```

Tests live in `tests/`. No tests exist yet -- write them as you build features.

## Key Commands

```bash
hotbunk status              # see all accounts and their state
hotbunk register <name>     # register current Claude credentials under a name
hotbunk switch <name>       # switch active account
hotbunk which               # show which account is active
hotbunk submit <type> -c "cmd"  # submit an automated job to the pool
hotbunk policy [-a name]    # view/edit account policy
```

## Dependencies

- click -- CLI framework
- rich -- terminal formatting
- fastapi + uvicorn -- planned dashboard API
- httpx -- HTTP client for future rate limit polling
- pyyaml -- policy files

## Style

- No em dashes in any public-facing text (READMEs, docstrings, CLI output). Use double hyphens (--) or rewrite.
- Keep modules small and focused. One concern per file.
- Type hints on all function signatures.
- Dataclasses over dicts for structured data.
